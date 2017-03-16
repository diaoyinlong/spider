/*当当图书详情表*/
/*DROP TABLE IF EXISTS `source_dangdang_bookinfo`;*/
CREATE TABLE `source_dangdang_bookinfo` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sourceId` int(11) unsigned NOT NULL,
  `bookName` varchar(255) NOT NULL DEFAULT '',
  `subName` varchar(255) NOT NULL DEFAULT '' COMMENT '短推',
  `author` varchar(255) NOT NULL DEFAULT '' COMMENT '作者',
  `press` varchar(255) NOT NULL DEFAULT '' COMMENT '出版社',
  `pubDate` varchar(255) NOT NULL DEFAULT '' COMMENT '出版日期',
  `printingDate` varchar(255) NOT NULL DEFAULT '' COMMENT '印刷日期',
  `price` float(9,2) NOT NULL DEFAULT '0.00' COMMENT '定价',
  `isbn` char(20) NOT NULL DEFAULT '',
  `edition` varchar(255) NOT NULL DEFAULT '' COMMENT '版次',
  `printingNum` varchar(255) NOT NULL DEFAULT '' COMMENT '印次',
  `pageNum` varchar(255) NOT NULL DEFAULT '' COMMENT '页数',
  `wordNum` varchar(255) NOT NULL DEFAULT '' COMMENT '字数',
  `pageSize` varchar(255) NOT NULL DEFAULT '' COMMENT '开本',
  `usedPaper` varchar(255) NOT NULL DEFAULT '' COMMENT '纸张',
  `binding` varchar(255) NOT NULL DEFAULT '' COMMENT '装订',
  `category` varchar(255) NOT NULL DEFAULT '' COMMENT '所属分类(当前图书所在分类，只一个)',
  `catNames` varchar(255) NOT NULL DEFAULT '' COMMENT '所属类目(可能有多个分类)',
  `imgPath` text NOT NULL COMMENT '图片存储路径',
  `relationProduct` text NOT NULL COMMENT '系列',
  `alsoView` text NOT NULL COMMENT '看了又看',
  `alsoBuy` text NOT NULL COMMENT '买了又买',
  `goodRatePercent` char(10) NOT NULL DEFAULT '' COMMENT '好评率',
  `goodRateCount` char(10) NOT NULL DEFAULT '' COMMENT '好评数',
  `editorComment` text NOT NULL COMMENT '编辑推荐',
  `contentIntroduction` text NOT NULL COMMENT '内容推荐',
  `authorIntroduction` text NOT NULL COMMENT '作者简介',
  `directory` text NOT NULL COMMENT '目录',
  `crawledTime` char(20) NOT NULL DEFAULT '' COMMENT '爬取时间',
  `updateTime` char(20) NOT NULL DEFAULT '' COMMENT '更新时间',
  `isQualified` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否为合格数据',
  `flag` tinyint(1) NOT NULL DEFAULT '0' COMMENT '标识字段 当前0代表未进行处理，1代表已经处理过',
  PRIMARY KEY (`id`),
  UNIQUE KEY `sourceId` (`sourceId`),
  KEY `isQualified` (`isQualified`),
  KEY `flag` (`flag`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*当当图书分类表*/
/*DROP TABLE IF EXISTS `source_dangdang_category`;*/
CREATE TABLE `source_dangdang_category` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '分类id',
  `url` varchar(255) NOT NULL COMMENT '分类url',
  `name` varchar(255) NOT NULL COMMENT '分类名称',
  `level` tinyint(1) NOT NULL COMMENT '第几级分类',
  `parentId` int(11) NOT NULL COMMENT '父级分类',
  `fullname` varchar(255) NOT NULL COMMENT '带层级分类名',
  PRIMARY KEY (`id`),
  KEY `fullname` (`fullname`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*当当图书-分类对应表*/
/*DROP TABLE IF EXISTS `source_dangdang_bookinfo_category`;*/
CREATE TABLE `source_dangdang_bookinfo_category` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `bookId` int(11) NOT NULL COMMENT '图书id',
  `catId` int(11) NOT NULL COMMENT '分类id',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*添加是否有货字段*/
ALTER TABLE source_dangdang_bookinfo ADD stock tinyint(1) DEFAULT NULL COMMENT '是否有货' AFTER directory;

/*添加索引*/
ALTER TABLE source_dangdang_bookinfo ADD INDEX isbn(isbn);
ALTER TABLE source_dangdang_bookinfo ADD INDEX dealFlag(dealFlag);

alter table source_dangdang_bookinfo add dealFlag tinyint(1) not null default '0';
