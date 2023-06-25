-- Schemata
SELECT *
FROM region-eu.INFORMATION_SCHEMA.SCHEMATA;

-- Tables
SELECT *
FROM region-eu.INFORMATION_SCHEMA.TABLES;

-- Columns
SELECT table_catalog, table_schema, table_name, column_name, data_type
FROM region-eu.INFORMATION_SCHEMA.COLUMNS;


SELECT abstract,
       web_url,
       snippet,
       lead_paragraph,
       print_section,
       print_page,
       source,
       pub_date,
       document_type,
       news_desk,
       section_name,
       _id,
       word_count,
       uri,
       subsection_name
FROM `ny-times-article-db`.ny_times.interim_article
LIMIT 10
;

SELECT _id, web_url, headline
FROM `ny-times-article-db`.ny_times.interim_article
WHERE headline.kicker IS NOT NULL
  AND headline.main IS NOT NULL
LIMIT 10
;

SELECT _id, web_url, byline
FROM `ny-times-article-db`.ny_times.interim_article
LIMIT 10
-- Feature Engineering ideas
-- First and Second Author
;

SELECT _id, web_url, multimedia
FROM `ny-times-article-db`.ny_times.interim_article
LIMIT 10
-- Feature Engineering ideas
;

SELECT _id, web_url, keywords
FROM `ny-times-article-db`.ny_times.interim_article
LIMIT 10
-- Feature Engineering ideas
;

-- Simple Count
SELECT section_name,
       COUNT(*)
FROM `ny-times-article-db`.ny_times.interim_article
GROUP BY 1
ORDER BY 2 desc
;

-- Pivot
SELECT section_name,
       subsection_name,
       COUNT(*) as count
FROM `ny-times-article-db`.ny_times.interim_article
GROUP BY 1,2
ORDER BY 3 desc
PIVOT(SUM(count)) FOR section_name in ('U.S', 'Opinion', 'New York', 'Sports')
;