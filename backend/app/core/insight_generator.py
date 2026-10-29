"""Executive financial insight narrator and follow-up suggestion generator."""
from typing import List, Dict, Any


class InsightGenerator:
    """Translates financial query outputs into actionable executive insights."""

    @classmethod
    def format_currency(cls, val: float) -> str:
        """Format numbers as human-friendly currency strings."""
        if val is None:
            return "N/A"
        abs_val = abs(val)
        sign = "-" if val < 0 else ""
        if abs_val >= 1e12:
            return f"{sign}${abs_val / 1e12:.2f}T"
        elif abs_val >= 1e9:
            return f"{sign}${abs_val / 1e9:.2f}B"
        elif abs_val >= 1e6:
            return f"{sign}${abs_val / 1e6:.2f}M"
        return f"{sign}${abs_val:,.2f}"

    @classmethod
    def generate_rule_based_insight(
        cls, question: str, data: List[Dict[str, Any]], template_id: str = ""
    ) -> str:
        """Generate executive commentary using deterministic financial rules."""
        if not data:
            return "No financial records matched the specified criteria or fiscal period."

        total_rows = len(data)

        if total_rows == 1:
            row = data[0]
            fy = row.get("fiscal_year_end") or row.get("end") or "selected period"
            points = []
            for k, v in row.items():
                if k in ["end", "fiscal_year_end", "start"]:
                    continue
                label = k.replace("_", " ").title()
                if isinstance(v, (int, float)):
                    if "pct" in k or "margin" in k:
                        points.append(f"• **{label}**: {v:.2f}%")
                    elif "ratio" in k:
                        points.append(f"• **{label}**: {v:.2f}x")
                    elif abs(v) > 1e6:
                        points.append(f"• **{label}**: {cls.format_currency(v)}")
                    else:
                        points.append(f"• **{label}**: {v:,.2f}")
            return f"### Executive Summary for {fy}\n\n" + "\n".join(points)

        # Multi-row time series summary
        first_row = data[0]
        last_row = data[-1]
        start_year = str(first_row.get("fiscal_year_end") or first_row.get("end"))[:4]
        end_year = str(last_row.get("fiscal_year_end") or last_row.get("end"))[:4]

        # Analyze key trends
        insights = [
            f"Analysis across **{total_rows} fiscal periods** ({start_year} to {end_year}):"
        ]

        if "revenue_billion" in last_row and "revenue_billion" in first_row:
            rev_start = first_row["revenue_billion"]
            rev_end = last_row["revenue_billion"]
            growth = ((rev_end - rev_start) / rev_start * 100) if rev_start else 0
            direction = "expanded" if growth > 0 else "contracted"
            insights.append(
                f"• Topline revenue {direction} from **${rev_start:.2f}B** to **${rev_end:.2f}B** ({growth:+.1f}% overall change)."
            )

        if "gross_margin_pct" in last_row:
            gm_latest = last_row["gross_margin_pct"]
            insights.append(
                f"• Latest reported Gross Margin stood at **{gm_latest:.2f}%**, reflecting high operational pricing power."
            )

        if "current_ratio" in last_row:
            cr_latest = last_row["current_ratio"]
            insights.append(
                f"• Latest Current Ratio is **{cr_latest:.2f}x**, aligned with Apple's negative working capital cash-generation strategy."
            )

        if "estimated_ccc_days" in last_row:
            ccc_latest = last_row["estimated_ccc_days"]
            insights.append(
                f"• Cash Conversion Cycle stands at **{ccc_latest:.1f} days** (negative CCC allows suppliers to fund ongoing operations)."
            )

        return "\n\n".join(insights)

    @classmethod
    def generate_suggested_followups(
        cls, question: str, data: List[Dict[str, Any]], template_id: str = ""
    ) -> List[str]:
        """Suggest smart follow-up executive inquiries."""
        q_lower = question.lower()
        if "margin" in q_lower or "profitability" in q_lower:
            return [
                "Show year-over-year margin expansion trends",
                "Compare operating cash flow with net income",
                "What was the revenue and gross margin in 2025?",
            ]
        elif "working capital" in q_lower or "liquidity" in q_lower:
            return [
                "What is Apple's Cash Conversion Cycle (CCC)?",
                "How does accounts receivable compare to revenue?",
                "What is the total liabilities-to-equity ratio?",
            ]
        elif "revenue" in q_lower or "sales" in q_lower:
            return [
                "Show multi-stage profitability margins over time",
                "Compare revenue growth vs accounts receivable growth",
                "What was the operating cash flow in 2024?",
            ]
        else:
            return [
                "Show executive financial health summary for 2025",
                "What are the historical profitability margins?",
                "Show Apple's cash conversion cycle breakdown",
            ]
