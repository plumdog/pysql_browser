SELECT
		*
FROM
		information_schema.KEY_COLUMN_USAGE
WHERE
		TABLE_NAME = {tab}
	AND
		TABLE_SCHEMA = {db}
	AND
		REFERENCED_TABLE_NAME IS NOT NULL
