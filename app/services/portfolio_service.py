"""Portfolio service for CRUD operations and calculations."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

from app.models.portfolio import (
    AggregatedPosition,
    HoldingPerformance,
    Portfolio,
    PortfolioHistory,
    PortfolioPerformance,
    PortfolioSnapshot,
    Position,
)
from app.models.stock import StockAnalysis
from app.services.stock_service import StockService
from app.utils.exceptions import PortfolioError, PositionNotFoundError


class PortfolioService:
    """Service for portfolio management and calculations."""

    def __init__(self, db_path: str, stock_service: StockService):
        """
        Initialize the portfolio service.

        Args:
            db_path: Path to SQLite database file
            stock_service: StockService for fetching current prices
        """
        self.db_path = db_path
        self.stock_service = stock_service
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database schema if not exists."""
        # Create parent directory if needed
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol VARCHAR(10) NOT NULL,
                    shares REAL NOT NULL CHECK (shares > 0),
                    purchase_price REAL NOT NULL CHECK (purchase_price > 0),
                    purchase_date DATE NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_positions_symbol
                    ON positions(symbol);

                CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_date DATE NOT NULL UNIQUE,
                    total_value REAL NOT NULL,
                    total_cost_basis REAL NOT NULL,
                    total_gain REAL NOT NULL,
                    total_gain_pct REAL NOT NULL,
                    num_positions INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_snapshots_date
                    ON portfolio_snapshots(snapshot_date);
            """
            )

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ============ CRUD Operations ============

    def add_position(
        self,
        symbol: str,
        shares: float,
        purchase_price: float,
        purchase_date: date,
        notes: Optional[str] = None,
    ) -> Position:
        """Add a new position to the portfolio."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO positions (symbol, shares, purchase_price, purchase_date, notes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    symbol.upper(),
                    shares,
                    purchase_price,
                    purchase_date.isoformat(),
                    notes,
                ),
            )
            position_id = cursor.lastrowid
            conn.commit()

        return Position(
            id=position_id,
            symbol=symbol.upper(),
            shares=shares,
            purchase_price=purchase_price,
            purchase_date=purchase_date,
            notes=notes,
        )

    def remove_position(self, position_id: int) -> bool:
        """Remove a position by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM positions WHERE id = ?",
                (position_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def update_position(
        self,
        position_id: int,
        shares: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> Position:
        """Update an existing position."""
        updates = []
        params: List = []

        if shares is not None:
            updates.append("shares = ?")
            params.append(shares)
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)

        if not updates:
            raise PortfolioError("No updates specified")

        params.append(position_id)

        with self._get_connection() as conn:
            conn.execute(
                f"UPDATE positions SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                params,
            )
            conn.commit()

        return self.get_position(position_id)

    def get_position(self, position_id: int) -> Position:
        """Get a single position by ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM positions WHERE id = ?",
                (position_id,),
            ).fetchone()

            if not row:
                raise PositionNotFoundError(f"Position {position_id} not found")

            return self._row_to_position(row)

    def get_all_positions(self) -> List[Position]:
        """Get all positions from the database."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM positions ORDER BY symbol, purchase_date"
            ).fetchall()

        return [self._row_to_position(row) for row in rows]

    def get_positions_by_symbol(self, symbol: str) -> List[Position]:
        """Get all positions for a specific symbol."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM positions WHERE symbol = ? ORDER BY purchase_date",
                (symbol.upper(),),
            ).fetchall()

        return [self._row_to_position(row) for row in rows]

    # ============ Portfolio Calculations ============

    def get_portfolio(self, include_prices: bool = True) -> Portfolio:
        """
        Get complete portfolio with current prices and calculations.

        Args:
            include_prices: Whether to fetch current prices (slower but complete)
        """
        positions = self.get_all_positions()

        if not positions:
            return Portfolio()

        # Fetch current prices for all unique symbols
        symbols = list(set(p.symbol for p in positions))
        price_data: Dict[str, StockAnalysis] = {}

        if include_prices:
            for symbol in symbols:
                try:
                    price_data[symbol] = self.stock_service.get_stock_analysis(symbol)
                except Exception:
                    pass  # Skip symbols that fail to fetch

        # Enrich positions with current data
        enriched_positions = []
        for position in positions:
            position.cost_basis = position.shares * position.purchase_price

            if position.symbol in price_data:
                analysis = price_data[position.symbol]
                position.current_price = analysis.current_price

                if analysis.current_price:
                    position.current_value = position.shares * analysis.current_price
                    position.unrealized_gain = position.current_value - position.cost_basis
                    position.unrealized_gain_pct = (
                        (position.unrealized_gain / position.cost_basis) * 100
                        if position.cost_basis > 0
                        else 0
                    )

                if analysis.current_price and analysis.previous_close:
                    position.day_change = (
                        analysis.current_price - analysis.previous_close
                    ) * position.shares
                    position.day_change_pct = (
                        (analysis.current_price - analysis.previous_close)
                        / analysis.previous_close
                    ) * 100

            enriched_positions.append(position)

        # Build aggregated positions
        aggregated = self._aggregate_positions(enriched_positions, price_data)

        # Calculate portfolio totals
        total_cost_basis = sum(p.cost_basis or 0 for p in enriched_positions)
        total_current_value = sum(p.current_value or 0 for p in enriched_positions)
        total_unrealized_gain = total_current_value - total_cost_basis
        total_day_change = sum(p.day_change or 0 for p in enriched_positions)

        # Calculate sector allocation
        sector_allocation: Dict[str, float] = {}
        for agg in aggregated:
            if agg.sector and agg.current_value and total_current_value > 0:
                if agg.sector not in sector_allocation:
                    sector_allocation[agg.sector] = 0
                sector_allocation[agg.sector] += (
                    agg.current_value / total_current_value
                ) * 100

        return Portfolio(
            positions=enriched_positions,
            aggregated=aggregated,
            total_cost_basis=total_cost_basis,
            total_current_value=total_current_value,
            total_unrealized_gain=total_unrealized_gain,
            total_unrealized_gain_pct=(
                (total_unrealized_gain / total_cost_basis) * 100
                if total_cost_basis > 0
                else 0
            ),
            total_day_change=total_day_change,
            total_day_change_pct=(
                (total_day_change / (total_current_value - total_day_change)) * 100
                if (total_current_value - total_day_change) > 0
                else 0
            ),
            num_positions=len(enriched_positions),
            num_symbols=len(symbols),
            sector_allocation=sector_allocation,
        )

    def _aggregate_positions(
        self,
        positions: List[Position],
        price_data: Dict[str, StockAnalysis],
    ) -> List[AggregatedPosition]:
        """Aggregate positions by symbol."""
        symbol_groups: Dict[str, List[Position]] = {}

        for position in positions:
            if position.symbol not in symbol_groups:
                symbol_groups[position.symbol] = []
            symbol_groups[position.symbol].append(position)

        aggregated = []
        total_portfolio_value = sum(p.current_value or 0 for p in positions)

        for symbol, lots in symbol_groups.items():
            total_shares = sum(p.shares for p in lots)
            total_cost = sum(p.shares * p.purchase_price for p in lots)
            average_cost = total_cost / total_shares if total_shares > 0 else 0

            current_price = None
            current_value = None
            sector = None
            industry = None

            if symbol in price_data:
                analysis = price_data[symbol]
                current_price = analysis.current_price
                sector = analysis.info.sector
                industry = analysis.info.industry
                if current_price:
                    current_value = total_shares * current_price

            unrealized_gain = (current_value - total_cost) if current_value else None
            unrealized_gain_pct = (
                (unrealized_gain / total_cost) * 100
                if unrealized_gain is not None and total_cost > 0
                else None
            )

            weight_pct = (
                (current_value / total_portfolio_value) * 100
                if current_value and total_portfolio_value > 0
                else None
            )

            aggregated.append(
                AggregatedPosition(
                    symbol=symbol,
                    total_shares=total_shares,
                    total_cost_basis=total_cost,
                    average_cost=average_cost,
                    current_price=current_price,
                    current_value=current_value,
                    unrealized_gain=unrealized_gain,
                    unrealized_gain_pct=unrealized_gain_pct,
                    weight_pct=weight_pct,
                    sector=sector,
                    industry=industry,
                    lots=lots,
                )
            )

        # Sort by current value (largest first)
        aggregated.sort(key=lambda x: x.current_value or 0, reverse=True)
        return aggregated

    def _row_to_position(self, row: sqlite3.Row) -> Position:
        """Convert database row to Position model."""
        return Position(
            id=row["id"],
            symbol=row["symbol"],
            shares=row["shares"],
            purchase_price=row["purchase_price"],
            purchase_date=date.fromisoformat(row["purchase_date"]),
            notes=row["notes"],
            created_at=(
                datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
            ),
            updated_at=(
                datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
            ),
        )

    # ============ History & Snapshots ============

    def save_snapshot(self, portfolio: Portfolio) -> PortfolioSnapshot:
        """
        Save a snapshot of the current portfolio value.
        Only one snapshot per day is kept (upserts on date).
        """
        today = date.today()
        snapshot = PortfolioSnapshot(
            snapshot_date=today,
            total_value=portfolio.total_current_value,
            total_cost_basis=portfolio.total_cost_basis,
            total_gain=portfolio.total_unrealized_gain,
            total_gain_pct=portfolio.total_unrealized_gain_pct,
            num_positions=portfolio.num_positions,
        )

        with self._get_connection() as conn:
            # Upsert: replace if date exists
            conn.execute(
                """
                INSERT INTO portfolio_snapshots
                    (snapshot_date, total_value, total_cost_basis, total_gain, total_gain_pct, num_positions)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(snapshot_date) DO UPDATE SET
                    total_value = excluded.total_value,
                    total_cost_basis = excluded.total_cost_basis,
                    total_gain = excluded.total_gain,
                    total_gain_pct = excluded.total_gain_pct,
                    num_positions = excluded.num_positions
                """,
                (
                    today.isoformat(),
                    snapshot.total_value,
                    snapshot.total_cost_basis,
                    snapshot.total_gain,
                    snapshot.total_gain_pct,
                    snapshot.num_positions,
                ),
            )
            conn.commit()

        return snapshot

    def get_history(self, days: int = 90) -> PortfolioHistory:
        """
        Get portfolio history for the specified number of days.

        Args:
            days: Number of days of history to retrieve (default 90)

        Returns:
            PortfolioHistory with snapshots and summary metrics
        """
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM portfolio_snapshots
                WHERE snapshot_date >= date('now', ?)
                ORDER BY snapshot_date ASC
                """,
                (f"-{days} days",),
            ).fetchall()

        if not rows:
            return PortfolioHistory()

        snapshots = [
            PortfolioSnapshot(
                id=row["id"],
                snapshot_date=date.fromisoformat(row["snapshot_date"]),
                total_value=row["total_value"],
                total_cost_basis=row["total_cost_basis"],
                total_gain=row["total_gain"],
                total_gain_pct=row["total_gain_pct"],
                num_positions=row["num_positions"],
                created_at=(
                    datetime.fromisoformat(row["created_at"])
                    if row["created_at"]
                    else None
                ),
            )
            for row in rows
        ]

        # Calculate summary metrics
        first = snapshots[0]
        last = snapshots[-1]

        # Find high and low
        high_snapshot = max(snapshots, key=lambda s: s.total_value)
        low_snapshot = min(snapshots, key=lambda s: s.total_value)

        total_change = last.total_value - first.total_value
        total_change_pct = (
            (total_change / first.total_value) * 100 if first.total_value > 0 else 0
        )

        return PortfolioHistory(
            snapshots=snapshots,
            earliest_date=first.snapshot_date,
            latest_date=last.snapshot_date,
            starting_value=first.total_value,
            current_value=last.total_value,
            total_change=total_change,
            total_change_pct=total_change_pct,
            high_value=high_snapshot.total_value,
            high_date=high_snapshot.snapshot_date,
            low_value=low_snapshot.total_value,
            low_date=low_snapshot.snapshot_date,
        )

    # ============ Performance Analysis ============

    def get_performance(self, portfolio: Portfolio) -> PortfolioPerformance:
        """
        Calculate performance breakdown by holdings.

        Args:
            portfolio: Portfolio with current prices

        Returns:
            PortfolioPerformance with per-holding contribution analysis
        """
        if not portfolio.aggregated:
            return PortfolioPerformance()

        total_gain = portfolio.total_unrealized_gain
        holdings = []

        for agg in portfolio.aggregated:
            if agg.current_value is None or agg.unrealized_gain is None:
                continue

            # Calculate contribution to total portfolio gain/loss
            contribution_pct = (
                (agg.unrealized_gain / abs(total_gain)) * 100
                if total_gain != 0
                else 0
            )

            # If the holding gain is opposite sign of total, contribution is negative
            if total_gain > 0 and agg.unrealized_gain < 0:
                contribution_pct = -abs(contribution_pct)
            elif total_gain < 0 and agg.unrealized_gain > 0:
                contribution_pct = -abs(contribution_pct)

            holdings.append(
                HoldingPerformance(
                    symbol=agg.symbol,
                    current_value=agg.current_value,
                    cost_basis=agg.total_cost_basis,
                    unrealized_gain=agg.unrealized_gain,
                    unrealized_gain_pct=agg.unrealized_gain_pct or 0,
                    weight_pct=agg.weight_pct or 0,
                    contribution_pct=contribution_pct,
                    sector=agg.sector,
                )
            )

        # Sort by unrealized gain for top gainers/losers
        sorted_by_gain = sorted(holdings, key=lambda h: h.unrealized_gain, reverse=True)
        top_gainers = [h for h in sorted_by_gain if h.unrealized_gain > 0][:5]
        top_losers = [h for h in reversed(sorted_by_gain) if h.unrealized_gain < 0][:5]

        # Calculate sector performance
        sector_gains: Dict[str, float] = {}
        sector_values: Dict[str, float] = {}
        for h in holdings:
            sector = h.sector or "Unknown"
            sector_gains[sector] = sector_gains.get(sector, 0) + h.unrealized_gain
            sector_values[sector] = sector_values.get(sector, 0) + h.cost_basis

        sector_performance = {
            sector: (gain / sector_values[sector]) * 100 if sector_values[sector] > 0 else 0
            for sector, gain in sector_gains.items()
        }

        return PortfolioPerformance(
            holdings=sorted_by_gain,
            top_gainers=top_gainers,
            top_losers=top_losers,
            total_value=portfolio.total_current_value,
            total_cost_basis=portfolio.total_cost_basis,
            total_gain=total_gain,
            total_gain_pct=portfolio.total_unrealized_gain_pct,
            sector_performance=sector_performance,
        )
