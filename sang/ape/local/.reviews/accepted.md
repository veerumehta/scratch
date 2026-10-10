# Findings weighed and lived with: `path :: slug`, one per line.
# The page dropdowns list every tenant with a published pack when PLATO_TENANTS is unset, on a
# deployed tier too (decided for dev-daily); a deployed tier that wants no list sets PLATO_TENANTS.
plato/api/info.py :: page-tenants-bypasses-wiring-rule
