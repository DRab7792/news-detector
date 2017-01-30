-- phpMyAdmin SQL Dump
-- version 4.5.2
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: Jan 30, 2017 at 05:54 AM
-- Server version: 10.1.10-MariaDB
-- PHP Version: 5.6.19

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";

--
-- Database: `news`
--

-- --------------------------------------------------------

--
-- Stand-in structure for view `articlelinks`
--
CREATE TABLE `articlelinks` (
`id` int(11)
,`event` int(11)
,`source` int(11)
,`weight` bigint(21)
);

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
  `source_id` varchar(200) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `eventLinks`
--

CREATE TABLE `eventLinks` (
  `id` int(11) NOT NULL,
  `event_a` int(11) NOT NULL,
  `event_b` int(11) NOT NULL,
  `distance` float NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `events`
--

CREATE TABLE `events` (
  `id` int(11) NOT NULL,
  `updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `who` text NOT NULL,
  `what` text NOT NULL,
  `loc` text NOT NULL,
  `time` text NOT NULL,
  `categories` text NOT NULL,
  `rank` float NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

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
-- Structure for view `articlelinks`
--
DROP TABLE IF EXISTS `articlelinks`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `articlelinks`  AS  select `articles`.`id` AS `id`,`articles`.`event` AS `event`,`articles`.`source` AS `source`,count(`articles`.`id`) AS `weight` from `articles` group by `articles`.`event`,`articles`.`source` ;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `articles`
--
ALTER TABLE `articles`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `eventLinks`
--
ALTER TABLE `eventLinks`
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
-- AUTO_INCREMENT for table `articles`
--
ALTER TABLE `articles`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;
--
-- AUTO_INCREMENT for table `eventLinks`
--
ALTER TABLE `eventLinks`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `events`
--
ALTER TABLE `events`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;
--
-- AUTO_INCREMENT for table `sources`
--
ALTER TABLE `sources`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=642;