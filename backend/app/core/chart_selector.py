"""Dynamic chart visualization selector based on data topology and financial semantics."""
from typing import List, Dict, Any, Optional
from backend.app.models.response import ChartConfig


class ChartSelector:
    """Infers optimal visualization topology for financial management dashboards."""

    @classmethod
    def select_chart(
        cls,
        question: str,
        data: List[Dict[str, Any]],
        template_chart_type: Optional[str] = None,
        template_title: Optional[str] = None,
        chart_preference: str = "auto",
    ) -> Optional[ChartConfig]:
        """Generate frontend chart configuration based on data rows and metadata."""
        if not data:
            return None

        row_count = len(data)
        columns = list(data[0].keys())

        # If user explicitly preferred a specific chart type
        if chart_preference != "auto" and chart_preference in ["line", "bar", "pie", "table", "kpi_card"]:
            chosen_type = chart_preference
        elif row_count == 1:
            chosen_type = "kpi_card"
        elif template_chart_type:
            chosen_type = template_chart_type
        else:
            # Heuristic selection
            has_date_axis = any(col in ["end", "fiscal_year_end", "start", "year"] for col in columns)
            if has_date_axis and row_count > 1:
                chosen_type = "line"
            elif row_count <= 8:
                chosen_type = "bar"
            else:
                chosen_type = "table"

        # Determine X axis
        x_axis = "fiscal_year_end" if "fiscal_year_end" in columns else ("end" if "end" in columns else columns[0])

        # Determine Y axis and numeric series
        numeric_columns = [
            col
            for col in columns
            if col not in ["end", "fiscal_year_end", "start", "year"]
            and isinstance(data[0].get(col), (int, float))
            and data[0].get(col) is not None
        ]

        if not numeric_columns:
            y_axis = columns[1] if len(columns) > 1 else columns[0]
            series = []
        else:
            y_axis = numeric_columns[0]
            palette = ["#0071E3", "#34C759", "#FF9500", "#AF52DE", "#FF3B30", "#5AC8FA"]
            series = [
                {
                    "dataKey": col,
                    "label": col.replace("_", " ").title(),
                    "color": palette[i % len(palette)],
                }
                for i, col in enumerate(numeric_columns[:4])
            ]

        # Determine format type
        format_type = "number"
        if any("pct" in col or "margin" in col or "ratio" in col for col in numeric_columns):
            format_type = "percentage"
        elif any("billion" in col or "revenue" in col or "assets" in col or "income" in col for col in numeric_columns):
            format_type = "currency"

        title = template_title or cls._generate_title(question, chosen_type)

        return ChartConfig(
            chart_type=chosen_type,
            title=title,
            x_axis=x_axis,
            y_axis=y_axis,
            series=series,
            format_type=format_type,
        )

    @staticmethod
    def _generate_title(question: str, chart_type: str) -> str:
        clean_q = question.strip().rstrip("?")
        if len(clean_q) > 60:
            clean_q = clean_q[:57] + "..."
        return f"{clean_q} ({chart_type.replace('_', ' ').title()})"
