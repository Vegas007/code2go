-- Selecting all users that are instructors
SELECT * FROM user WHERE auth_grade = 2;

-- Selecting all users that are students
SELECT * FROM user WHERE auth_grade = 1;

-- Selecting courses that have category marked as 'python'
SELECT * FROM course WHERE category = 'python';

-- Selecting courses ordered by last_updated date in descending order and limiting the result to 5
SELECT * FROM course ORDER BY last_updated DESC LIMIT 5;

-- Selecting courses that have price less than 50.0
SELECT * FROM course WHERE price < 50.0;

-- Selecting courses by email of the instructor
SELECT c.*
FROM user uc
         JOIN course c ON c.id = uc.id
JOIN user u ON uc.id = u.id
WHERE u.email = 'deeaganea@gmail.com';

-- Selecting courses that have 'C++' in their title
SELECT * FROM course WHERE title LIKE '%C++%';

-- Reduce the price of all courses by 50% (discount)
UPDATE course SET price = price * 0.5 WHERE price > 0.0;



