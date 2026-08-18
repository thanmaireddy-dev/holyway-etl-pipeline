-- analytics.sql
-- HolyWay Data Engineering Pipeline - SQL Analytics

-- 1. Count churches by denomination
SELECT denomination, COUNT(*) as church_count
FROM churches
GROUP BY denomination
ORDER BY church_count DESC;

-- 2. Count churches by city (Top 10)
SELECT city, COUNT(*) as church_count
FROM churches
GROUP BY city
ORDER BY church_count DESC
LIMIT 10;

-- 3. Count services by language
SELECT language, COUNT(*) as service_count
FROM services
WHERE language IS NOT NULL AND language != ''
GROUP BY language
ORDER BY service_count DESC;

-- 4. Find churches with the highest number of services (Top 5)
SELECT name, denomination, city, service_count
FROM churches
ORDER BY service_count DESC
LIMIT 5;

-- 5. Find churches with missing coordinates
SELECT name, city, address
FROM churches
WHERE latitude IS NULL OR longitude IS NULL;

-- 6. Calculate average number of services per church by denomination
SELECT denomination, ROUND(AVG(service_count), 2) as avg_services_per_church
FROM churches
GROUP BY denomination
ORDER BY avg_services_per_church DESC;

-- 7. Find churches that have no recorded services
SELECT name, denomination, city
FROM churches
WHERE service_count = 0;

-- 8. Find the number of service records for each day
SELECT day, COUNT(*) as service_count
FROM services
GROUP BY day
ORDER BY service_count DESC;

-- 9. Find churches missing phone numbers
SELECT name, city, address
FROM churches
WHERE phone IS NULL OR phone = 'To be updated' OR phone = '';

-- 10. Find service rows missing time or language
SELECT church_name, day, time, language, note
FROM services
WHERE time IS NULL OR time = '' OR language IS NULL OR language = '';
