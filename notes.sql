SELECT b.id, b.source_id, b.source, c.event, c.id, c.source_id, c.source, c.event
FROM `articleLinks` a 
INNER JOIN `articles` b
ON a.source = b.id 
INNER JOIN `articles` c
ON a.dest = c.id AND
a.weight = 30;

SELECT c.id
FROM `articleLinks` a 
INNER JOIN `articles` b
ON a.source = b.id 
INNER JOIN `articles` c
ON a.dest = c.id AND
a.weight = 30;

DELETE a FROM `articles` a, `articles` b WHERE a.id > b.id AND a.source_id = b.name


SELECT a.id as `id`, a.title as `article_title`, b.title as `source_title`
FROM `articles` a 
INNER JOIN `sources` b
ON a.source = b.id;

-- Get the cumulative edge distribution

DROP PROCEDURE IF EXISTS CumulativeEdgeDistro;

DELIMITER $$

CREATE PROCEDURE CumulativeEdgeDistro ()
BEGIN
	DECLARE i INT;
	DECLARE edges INT;
	DECLARE nodes INT;
	DECLARE density FLOAT;
	SET i = 0;
	SET nodes = (SELECT count(`id`) FROM `articles`);
	DROP TABLE IF EXISTS distro;
	CREATE TEMPORARY TABLE distro (`min_weight` INTEGER, `edges` INTEGER, `density` FLOAT);
	WHILE i < 30
	DO 
		SET i = i + 1;
		SET edges = (SELECT count(`id`) FROM articleLinks WHERE `weight` > i LIMIT 1);
		SET density = (2*edges)/(nodes * (nodes - 1));
		INSERT INTO distro (`min_weight`, `edges`, `density`) VALUES (i, edges, density);
	END WHILE;
	SELECT * FROM distro;
END $$

DELIMITER ;

CALL CumulativeEdgeDistro();