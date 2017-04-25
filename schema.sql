-- phpMyAdmin SQL Dump
-- version 4.5.2
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: Apr 24, 2017 at 06:04 AM
-- Server version: 10.1.10-MariaDB
-- PHP Version: 5.6.19

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";

--
-- Database: `news`
--

DELIMITER $$
--
-- Procedures
--
CREATE DEFINER=`root`@`localhost` PROCEDURE `CumulativeEdgeDistro` ()  BEGIN
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
END$$

DELIMITER ;

-- --------------------------------------------------------

--
-- Table structure for table `articleLinks`
--

CREATE TABLE `articleLinks` (
  `id` int(11) NOT NULL,
  `source` int(11) NOT NULL,
  `dest` int(11) NOT NULL,
  `weight` float NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `articles`
--

CREATE TABLE `articles` (
  `id` int(11) NOT NULL,
  `event` int(11) NOT NULL,
  `source` int(11) NOT NULL,
  `title` varchar(1000) NOT NULL,
  `url` varchar(300) NOT NULL,
  `description` text NOT NULL,
  `source_id` varchar(500) NOT NULL,
  `time` varchar(100) NOT NULL,
  `who` text NOT NULL,
  `what` text NOT NULL,
  `loc` text NOT NULL,
  `words` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `events`
--

CREATE TABLE `events` (
  `id` int(11) NOT NULL,
  `num_articles` int(11) NOT NULL,
  `keywords` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Stand-in structure for view `eventstats`
--
CREATE TABLE `eventstats` (
`event` int(11)
,`number_of_articles` bigint(21)
);

-- --------------------------------------------------------

--
-- Table structure for table `sources`
--

CREATE TABLE `sources` (
  `id` int(11) NOT NULL,
  `updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `title` varchar(1000) NOT NULL,
  `url` varchar(250) NOT NULL,
  `rss_feed` varchar(500) NOT NULL,
  `type` enum('Fake News','Satire','Extreme Bias','Conspiracy Theory','Rumor Mill','State News','Junk Science','Hate News','Clickbait','Proceed With Caution','Political','Credible') NOT NULL,
  `language` varchar(10) NOT NULL,
  `credible` tinyint(4) NOT NULL,
  `rank` float DEFAULT NULL,
  `description` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Structure for view `eventstats`
--
DROP TABLE IF EXISTS `eventstats`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `eventstats`  AS  select `articles`.`event` AS `event`,count(`articles`.`id`) AS `number_of_articles` from `articles` where (`articles`.`event` > 0) group by `articles`.`event` ;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `articleLinks`
--
ALTER TABLE `articleLinks`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `source` (`source`,`dest`);

--
-- Indexes for table `articles`
--
ALTER TABLE `articles`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `events`
--
ALTER TABLE `events`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `sources`
--
ALTER TABLE `sources`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `articleLinks`
--
ALTER TABLE `articleLinks`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3114001;
--
-- AUTO_INCREMENT for table `articles`
--
ALTER TABLE `articles`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4378;
--
-- AUTO_INCREMENT for table `sources`
--
ALTER TABLE `sources`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=642;