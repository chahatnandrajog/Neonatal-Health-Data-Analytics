-- KPI 1: Birth totals separated by year
SELECT
	year,
	SUM(births) AS Total_Births
FROM dbo.birth_totals
GROUP BY year
ORDER BY year;

-- KPI 1: Total Births (all years)
SELECT
	SUM(births) As Total_Births
FROM dbo.birth_totals;

-- KPI 2: Low birth weight rate
SELECT
	year,
	ROUND(
		100.0 * SUM(CASE
			WHEN TRY_CAST(birth_weight_code AS INT) BETWEEN 1 AND 5
			THEN births ELSE 0
		END)
		/
		NULLIF(SUM(CASE
			WHEN TRY_CAST(birth_weight_code AS INT) BETWEEN 1 AND 11
			THEN births ELSE 0
		END), 0),
		2
	) AS Low_Birth_Weight_Rate
FROM dbo.birth_weight
GROUP BY year
ORDER BY year;

--KPI 3: 