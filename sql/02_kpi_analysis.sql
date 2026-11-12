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