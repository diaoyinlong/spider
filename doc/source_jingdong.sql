/*京东图书详情表*/
/*DROP TABLE IF EXISTS `source_jingdong_bookinfo`;*/
CREATE TABLE `source_jingdong_bookinfo` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sourceId` int(11) unsigned NOT NULL,
  `bookName` varchar(255) NOT NULL,
  `author` varchar(255) DEFAULT NULL COMMENT '作者',
  `press` varchar(255) DEFAULT NULL COMMENT '出版社',
  `pubDate` varchar(255) DEFAULT NULL COMMENT '出版日期',
  `price` float(9,2) DEFAULT NULL COMMENT '定价',
  `isbn` char(20) DEFAULT NULL,
  `edition` varchar(255) DEFAULT NULL COMMENT '版次',
  `pageNum` varchar(255) COMMENT '页数',
  `wordNum` varchar(255) COMMENT '字数',
  `pageSize` varchar(255) COMMENT '开本',
  `usedPaper` varchar(255) COMMENT '纸张',
  `binding` varchar(255) DEFAULT NULL COMMENT '装订',
  `series` varchar(255) DEFAULT NULL COMMENT '丛书',
  `category` varchar(255) DEFAULT NULL COMMENT '所属分类(当前图书所在分类，只一个)',
  `imgPath` text DEFAULT NULL COMMENT '图片存储路径',
  `relationProduct` text DEFAULT NULL COMMENT '系列',
  `brand` varchar(255) DEFAULT NULL COMMENT '品牌',
  `language` varchar(255) DEFAULT NULL COMMENT '正文语种',
  `tag` text DEFAULT NULL COMMENT '标签',
  `popularItem` text DEFAULT NULL COMMENT '人气单品',
  `alsoView` text DEFAULT NULL COMMENT '看了又看',
  `alsoBuy` text DEFAULT NULL COMMENT '买了又买/达人选购',
  `hotRecommend` text DEFAULT NULL COMMENT '热门推荐',
  `goodRatePercent` char(10) DEFAULT NULL COMMENT '好评率',
  `goodRateCount` char(10) DEFAULT NULL COMMENT '好评数',
  `editorComment` text DEFAULT NULL COMMENT '编辑推荐',
  `contentIntroduction` text DEFAULT NULL COMMENT '内容推荐',
  `authorIntroduction` text DEFAULT NULL COMMENT '作者简介',
  `directory` text DEFAULT NULL COMMENT '目录',
  `crawledTime` char(20) DEFAULT NULL COMMENT '爬取时间',
  `updateTime` char(20) DEFAULT NULL COMMENT '更新时间',
  `isQualified` tinyint(1) NOT NULL DEFAULT 1 COMMENT '是否为合格数据',
  `flag` tinyint(1) NOT NULL DEFAULT '0' COMMENT '标识字段 当前0代表未进行处理，1代表已经处理过',
  PRIMARY KEY (`id`),
  UNIQUE KEY `sourceId` (`sourceId`),
  KEY `isQualified` (`isQualified`),
  KEY `flag` (`flag`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*京东图书分类表*/
/*DROP TABLE IF EXISTS `source_jingdong_category`;*/
CREATE TABLE `source_jingdong_category` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '分类id',
  `name` varchar(255) NOT NULL COMMENT '分类名称',
  `level` tinyint(1) NOT NULL COMMENT '第几级分类',
  `parentId` int(11) NOT NULL COMMENT '父级分类',
  `fullname` varchar(255) NOT NULL COMMENT '带层级分类名',
  PRIMARY KEY (`id`),
  KEY `fullname` (`fullname`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*京东图书-分类对应表*/
/*DROP TABLE IF EXISTS `source_jingdong_bookinfo_category`;*/
CREATE TABLE `source_jingdong_bookinfo_category` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `bookId` int(11) NOT NULL COMMENT '图书id',
  `catId` int(11) NOT NULL COMMENT '分类id',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/*添加是否有货字段*/
ALTER TABLE source_jingdong_bookinfo ADD stock tinyint(1) DEFAULT NULL COMMENT '是否有货' AFTER directory;

/*添加索引*/
ALTER TABLE source_jingdong_bookinfo ADD INDEX isbn(isbn);
ALTER TABLE source_jingdong_bookinfo ADD INDEX dealFlag(dealFlag);

alter table source_jingdong_bookinfo add dealFlag tinyint(1) not null default '0';
