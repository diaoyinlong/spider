/*豆瓣图书详情表*/
/*DROP TABLE IF EXISTS `source_douban_bookinfo`;*/
CREATE TABLE `source_douban_bookinfo` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sourceId` varchar(10) NOT NULL,
  `bookName` varchar(255) NOT NULL DEFAULT '',
  `author` varchar(255) NOT NULL DEFAULT '' COMMENT '作者',
  `press` varchar(255) NOT NULL DEFAULT '' COMMENT '出版社',
  `subTitle` varchar(255) NOT NULL DEFAULT '' COMMENT '副标题',
  `foreignName` varchar(255) NOT NULL DEFAULT '' COMMENT '外文书名',
  `translator` varchar(255) NOT NULL DEFAULT '' COMMENT '译者',
  `pubDate` varchar(255) NOT NULL DEFAULT '' COMMENT '出版日期',
  `pageNum` varchar(255) NOT NULL DEFAULT '' COMMENT '页数',
  `price` float(9,2) NOT NULL DEFAULT '0.00' COMMENT '价格',
  `binding` varchar(255) NOT NULL DEFAULT '' COMMENT '装订',
  `series` text NOT NULL COMMENT '丛书',
  `isbn` char(20) NOT NULL DEFAULT '',
  `avgRate` char(10) NOT NULL DEFAULT '' COMMENT '评分',
  `rateNum` char(10) NOT NULL DEFAULT '' COMMENT '总评价数',
  `contentIntroduction` varchar(255) NOT NULL DEFAULT '' COMMENT '内容简介',
  `authorIntroduction` text NOT NULL COMMENT '作者简介',
  `otherVersion` text NOT NULL COMMENT '其它版本',
  `douList` text NOT NULL COMMENT '豆列推荐',
  `imgPath` text NOT NULL COMMENT '图片',
  `tag` text NOT NULL COMMENT '标签',
  `directory` text NOT NULL COMMENT '目录',
  `alsoLike` text NOT NULL COMMENT '喜欢也喜欢',
  `priceCompare` text NOT NULL COMMENT '比价',
  `crawledTime` char(20) NOT NULL DEFAULT '' COMMENT '爬取时间',
  `updateTime` char(20) NOT NULL DEFAULT '' COMMENT '更新时间',
  `isQualified` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否为合格数据',
  `flag` tinyint(1) NOT NULL DEFAULT '0' COMMENT '标识字段 当前0代表未进行处理，1代表已经处理过',
  PRIMARY KEY (`id`),
  UNIQUE KEY `sourceId` (`sourceId`),
  KEY `isQualified` (`isQualified`),
  KEY `flag` (`flag`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*豆瓣图书分类表*/
/*DROP TABLE IF EXISTS `source_douban_category`;*/
CREATE TABLE `source_douban_category` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '分类id',
  `name` varchar(255) NOT NULL COMMENT '分类名称',
  PRIMARY KEY (`id`),
  KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*豆瓣图书-分类对应表*/
/*DROP TABLE IF EXISTS `source_douban_bookinfo_category`;*/
CREATE TABLE `source_douban_bookinfo_category` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `bookId` int(11) NOT NULL COMMENT '图书id',
  `catId` int(11) NOT NULL COMMENT '分类id',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*添加是否有货字段*/
ALTER TABLE source_douban_bookinfo ADD stock tinyint(1) DEFAULT NULL COMMENT '是否有货' AFTER priceCompare;

/*添加索引*/
ALTER TABLE source_douban_bookinfo ADD INDEX isbn(isbn);
ALTER TABLE source_douban_bookinfo ADD INDEX dealFlag(dealFlag);

alter table source_douban_bookinfo add dealFlag tinyint(1) not null default '0';
