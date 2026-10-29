"""SQL Safety Validator and Sanitizer using AST parsing and token heuristics."""
import re
from typing import Tuple, Set
import sqlglot
from sqlglot import exp


class SQLValidator:
    """Production-grade SQL safety validation engine."""

    ALLOWED_TABLES: Set[str] = {
        "income_statement",
        "balance_sheet",
        "cash_flow",
        "accounts_payable",
    }

    FORBIDDEN_KEYWORDS: Set[str] = {
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "CREATE",
        "TRUNCATE",
        "GRANT",
        "REVOKE",
        "EXEC",
        "EXECUTE",
        "CALL",
        "LOAD",
        "INTO OUTFILE",
        "INTO DUMPFILE",
        "INFORMATION_SCHEMA",
        "MYSQL",
        "PERFORMANCE_SCHEMA",
        "SYS",
        "SLEEP",
        "BENCHMARK",
    }

    MAX_QUERY_LENGTH: int = 5000

    @classmethod
    def sanitize(cls, sql: str) -> str:
        """Strip markdown ticks, trailing semicolons, and normalize whitespace."""
        if not sql:
            return ""
        # Remove markdown code fence ```sql ... ```
        cleaned = re.sub(r"^```(?:sql)?\s*", "", sql.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned.strip())
        # Strip trailing semicolons and spaces
        cleaned = cleaned.strip().rstrip(";")
        return cleaned.strip()

    @classmethod
    def validate(cls, sql: str) -> Tuple[bool, str]:
        """Validate if the SQL query is safe, read-only, and references allowed tables.
        
        Returns:
            Tuple[bool, str]: (is_valid, reason_or_error)
        """
        cleaned_sql = cls.sanitize(sql)
        if not cleaned_sql:
            return False, "Query cannot be empty"

        if len(cleaned_sql) > cls.MAX_QUERY_LENGTH:
            return False, f"Query exceeds max allowed length of {cls.MAX_QUERY_LENGTH} characters"

        # Check for multiple stacked statements
        # A semicolon not within quotes indicates stacked statements
        in_single = False
        in_double = False
        for char in cleaned_sql:
            if char == "'" and not in_double:
                in_single = not in_single
            elif char == '"' and not in_single:
                in_double = not in_double
            elif char == ";" and not in_single and not in_double:
                return False, "Multiple SQL statements separated by semicolons are forbidden"

        # Quick keyword check using regex word boundaries
        upper_sql = cleaned_sql.upper()
        for forbidden in cls.FORBIDDEN_KEYWORDS:
            if re.search(rf"\b{re.escape(forbidden)}\b", upper_sql):
                return False, f"Query contains forbidden keyword or command: {forbidden}"

        # AST parsing via sqlglot
        try:
            parsed_expressions = sqlglot.parse(cleaned_sql, read="mysql")
            if not parsed_expressions:
                return False, "Unable to parse SQL expression"
            if len(parsed_expressions) > 1:
                return False, "Multiple SQL statements detected via AST analysis"

            statement = parsed_expressions[0]
            if not isinstance(statement, (exp.Select, exp.Union)):
                return False, f"Only SELECT or UNION queries are permitted, got {type(statement).__name__}"

            # Collect CTE aliases so we don't treat them as unknown external tables
            cte_aliases: Set[str] = set()
            for cte in statement.find_all(exp.CTE):
                if cte.alias:
                    cte_aliases.add(cte.alias.lower())

            # Verify referenced tables
            tables = statement.find_all(exp.Table)
            for table in tables:
                table_name = table.name.lower()
                # If table matches a CTE or an allowed table or derived alias, allow
                if (
                    table_name not in cls.ALLOWED_TABLES
                    and table_name not in cte_aliases
                    and not table_name.startswith("sq_")
                ):
                    return False, f"Unauthorized table access: '{table_name}'. Only financial tables are allowed."

        except Exception as e:
            # Fallback regex checks if syntax is dialect-specific or parser fails
            if not upper_sql.strip().startswith(("SELECT", "WITH")):
                return False, f"Query must start with SELECT or WITH. Parse error: {str(e)}"

        return True, "Valid read-only query"
