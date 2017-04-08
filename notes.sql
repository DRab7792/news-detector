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