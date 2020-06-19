-- MySQL dump 10.16  Distrib 10.1.26-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: db
-- ------------------------------------------------------
-- Server version	10.1.26-MariaDB-0+deb9u1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group` (
  `id` varchar(0) DEFAULT NULL,
  `name` varchar(0) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group_permissions` (
  `id` varchar(0) DEFAULT NULL,
  `group_id` varchar(0) DEFAULT NULL,
  `permission_id` varchar(0) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_permission` (
  `id` tinyint(4) DEFAULT NULL,
  `content_type_id` tinyint(4) DEFAULT NULL,
  `codename` varchar(33) DEFAULT NULL,
  `name` varchar(40) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,1,'add_logentry','Can add log entry'),(2,1,'change_logentry','Can change log entry'),(3,1,'delete_logentry','Can delete log entry'),(4,2,'add_user','Can add user'),(5,2,'change_user','Can change user'),(6,2,'delete_user','Can delete user'),(7,3,'add_group','Can add group'),(8,3,'change_group','Can change group'),(9,3,'delete_group','Can delete group'),(10,4,'add_permission','Can add permission'),(11,4,'change_permission','Can change permission'),(12,4,'delete_permission','Can delete permission'),(13,5,'add_contenttype','Can add content type'),(14,5,'change_contenttype','Can change content type'),(15,5,'delete_contenttype','Can delete content type'),(16,6,'add_session','Can add session'),(17,6,'change_session','Can change session'),(18,6,'delete_session','Can delete session'),(19,7,'add_apikey','Can add api key'),(20,7,'change_apikey','Can change api key'),(21,7,'delete_apikey','Can delete api key'),(22,8,'add_apiaccess','Can add api access'),(23,8,'change_apiaccess','Can change api access'),(24,8,'delete_apiaccess','Can delete api access'),(25,9,'add_probe','Can add probe'),(26,9,'change_probe','Can change probe'),(27,9,'delete_probe','Can delete probe'),(28,10,'add_timeprofile','Can add time profile'),(29,10,'change_timeprofile','Can change time profile'),(30,10,'delete_timeprofile','Can delete time profile'),(31,11,'add_director','Can add director'),(32,11,'change_director','Can change director'),(33,11,'delete_director','Can delete director'),(34,12,'add_backend','Can add backend'),(35,12,'change_backend','Can change backend'),(36,12,'delete_backend','Can delete backend'),(37,13,'add_logicalcluster','Can add logical cluster'),(38,13,'change_logicalcluster','Can change logical cluster'),(39,13,'delete_logicalcluster','Can delete logical cluster'),(40,14,'add_dc','Can add dc'),(41,14,'change_dc','Can change dc'),(42,14,'delete_dc','Can delete dc'),(43,15,'add_historicalvcltemplate','Can add historical vcl template'),(44,15,'change_historicalvcltemplate','Can change historical vcl template'),(45,15,'delete_historicalvcltemplate','Can delete historical vcl template'),(46,16,'add_vcltemplate','Can add vcl template'),(47,16,'change_vcltemplate','Can change vcl template'),(48,16,'delete_vcltemplate','Can delete vcl template'),(49,17,'add_varnishserver','Can add varnish server'),(50,17,'change_varnishserver','Can change varnish server'),(51,17,'delete_varnishserver','Can delete varnish server'),(52,18,'add_historicalvcltemplateblock','Can add historical vcl template block'),(53,18,'change_historicalvcltemplateblock','Can change historical vcl template block'),(54,18,'delete_historicalvcltemplateblock','Can delete historical vcl template block'),(55,19,'add_vcltemplateblock','Can add vcl template block'),(56,19,'change_vcltemplateblock','Can change vcl template block'),(57,19,'delete_vcltemplateblock','Can delete vcl template block'),(58,20,'add_vclvariable','Can add vcl variable'),(59,20,'change_vclvariable','Can change vcl variable'),(60,20,'delete_vclvariable','Can delete vcl variable'),(61,21,'add_route','Can add route'),(62,21,'change_route','Can change route'),(63,21,'delete_route','Can delete route'),(64,22,'add_positiveurl','Can add positive url'),(65,22,'change_positiveurl','Can change positive url'),(66,22,'delete_positiveurl','Can delete positive url'),(67,23,'add_backendstatus','Can add backend status'),(68,23,'change_backendstatus','Can change backend status'),(69,23,'delete_backendstatus','Can delete backend status'),(70,24,'add_tag','Can add Tag'),(71,24,'change_tag','Can change Tag'),(72,24,'delete_tag','Can delete Tag'),(73,25,'add_taggeditem','Can add Tagged Item'),(74,25,'change_taggeditem','Can change Tagged Item'),(75,25,'delete_taggeditem','Can delete Tagged Item'),(76,26,'add_code','Can add code'),(77,26,'change_code','Can change code'),(78,26,'delete_code','Can delete code'),(79,27,'add_partial','Can add partial'),(80,27,'change_partial','Can change partial'),(81,27,'delete_partial','Can delete partial'),(82,28,'add_association','Can add association'),(83,28,'change_association','Can change association'),(84,28,'delete_association','Can delete association'),(85,29,'add_usersocialauth','Can add user social auth'),(86,29,'change_usersocialauth','Can change user social auth'),(87,29,'delete_usersocialauth','Can delete user social auth'),(88,30,'add_nonce','Can add nonce'),(89,30,'change_nonce','Can change nonce'),(90,30,'delete_nonce','Can delete nonce');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user` (
  `id` tinyint(4) DEFAULT NULL,
  `password` varchar(77) DEFAULT NULL,
  `last_login` varchar(10) DEFAULT NULL,
  `is_superuser` tinyint(4) DEFAULT NULL,
  `first_name` varchar(0) DEFAULT NULL,
  `last_name` varchar(0) DEFAULT NULL,
  `email` varchar(27) DEFAULT NULL,
  `is_staff` tinyint(4) DEFAULT NULL,
  `is_active` tinyint(4) DEFAULT NULL,
  `date_joined` varchar(10) DEFAULT NULL,
  `username` varchar(5) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'pbkdf2_sha256$36000$HSNx3yHNXG51$yggojN+90XWiHuGBK7YnrUZMWtMKpck45CsSel0JxUk=','2019-11-19',1,'','','admin@vaas.allegrogroup.com',1,1,'2019-11-13','admin');
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user_groups` (
  `id` varchar(0) DEFAULT NULL,
  `user_id` varchar(0) DEFAULT NULL,
  `group_id` varchar(0) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_groups`
--

LOCK TABLES `auth_user_groups` WRITE;
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` varchar(0) DEFAULT NULL,
  `user_id` varchar(0) DEFAULT NULL,
  `permission_id` varchar(0) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cluster_dc`
--

DROP TABLE IF EXISTS `cluster_dc`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cluster_dc` (
  `id` tinyint(4) DEFAULT NULL,
  `name` varchar(17) DEFAULT NULL,
  `symbol` varchar(3) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cluster_dc`
--

LOCK TABLES `cluster_dc` WRITE;
/*!40000 ALTER TABLE `cluster_dc` DISABLE KEYS */;
INSERT INTO `cluster_dc` VALUES (1,'First datacenter','dc1'),(2,'Second datacenter','dc2');
/*!40000 ALTER TABLE `cluster_dc` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cluster_historicalvcltemplate`
--

DROP TABLE IF EXISTS `cluster_historicalvcltemplate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cluster_historicalvcltemplate` (
  `id` varchar(0) DEFAULT NULL,
  `name` varchar(0) DEFAULT NULL,
  `content` varchar(0) DEFAULT NULL,
  `version` varchar(0) DEFAULT NULL,
  `comment` varchar(0) DEFAULT NULL,
  `history_id` varchar(0) DEFAULT NULL,
  `history_date` varchar(0) DEFAULT NULL,
  `history_user_id` varchar(0) DEFAULT NULL,
  `history_type` varchar(0) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cluster_historicalvcltemplate`
--

LOCK TABLES `cluster_historicalvcltemplate` WRITE;
/*!40000 ALTER TABLE `cluster_historicalvcltemplate` DISABLE KEYS */;
/*!40000 ALTER TABLE `cluster_historicalvcltemplate` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cluster_historicalvcltemplateblock`
--

DROP TABLE IF EXISTS `cluster_historicalvcltemplateblock`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cluster_historicalvcltemplateblock` (
  `id` varchar(0) DEFAULT NULL,
  `tag` varchar(0) DEFAULT NULL,
  `content` varchar(0) DEFAULT NULL,
  `template_id` varchar(0) DEFAULT NULL,
  `history_id` varchar(0) DEFAULT NULL,
  `history_date` varchar(0) DEFAULT NULL,
  `history_user_id` varchar(0) DEFAULT NULL,
  `history_type` varchar(0) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cluster_historicalvcltemplateblock`
--

LOCK TABLES `cluster_historicalvcltemplateblock` WRITE;
/*!40000 ALTER TABLE `cluster_historicalvcltemplateblock` DISABLE KEYS */;
/*!40000 ALTER TABLE `cluster_historicalvcltemplateblock` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cluster_logicalcluster`
--

DROP TABLE IF EXISTS `cluster_logicalcluster`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cluster_logicalcluster` (
  `id` tinyint(4) DEFAULT NULL,
  `name` varchar(19) DEFAULT NULL,
  `reload_timestamp` varchar(10) DEFAULT NULL,
  `error_timestamp` varchar(10) DEFAULT NULL,
  `last_error_info` varchar(0) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cluster_logicalcluster`
--

LOCK TABLES `cluster_logicalcluster` WRITE;
/*!40000 ALTER TABLE `cluster_logicalcluster` DISABLE KEYS */;
INSERT INTO `cluster_logicalcluster` VALUES (1,'cluster1_siteA_test','2019-11-19','2019-11-13',''),(2,'cluster2_siteB_test','2019-11-18','2019-11-13',''),(3,'cluster3_siteA_dev','2019-11-18','2019-11-13',''),(4,'cluster4_siteC_prod','2019-11-18','2019-11-13','');
/*!40000 ALTER TABLE `cluster_logicalcluster` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cluster_varnishserver`
--

DROP TABLE IF EXISTS `cluster_varnishserver`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cluster_varnishserver` (
  `id` tinyint(4) DEFAULT NULL,
  `ip` varchar(13) DEFAULT NULL,
  `hostname` varchar(11) DEFAULT NULL,
  `cluster_weight` tinyint(4) DEFAULT NULL,
  `http_port` smallint(6) DEFAULT NULL,
  `port` smallint(6) DEFAULT NULL,
  `secret` varchar(36) DEFAULT NULL,
  `status` varchar(6) DEFAULT NULL,
  `dc_id` tinyint(4) DEFAULT NULL,
  `template_id` tinyint(4) DEFAULT NULL,
  `cluster_id` tinyint(4) DEFAULT NULL,
  `is_canary` tinyint(4) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cluster_varnishserver`
--

LOCK TABLES `cluster_varnishserver` WRITE;
/*!40000 ALTER TABLE `cluster_varnishserver` DISABLE KEYS */;
INSERT INTO `cluster_varnishserver` VALUES (2,'192.168.199.3','varnish-4',1,6081,6082,'edcf6c52-6f93-4d0d-82b9-cd74239146b0','active',1,2,1,0),(3,'192.168.199.4','varnish-4.1',1,6081,6082,'edcf6c52-6f93-4d0d-82b9-cd74239146b0','active',1,2,2,0),(4,'192.168.199.6','varnish-6',1,6081,6082,'edcf6c52-6f93-4d0d-82b9-cd74239146b0','active',1,2,1,0);
/*!40000 ALTER TABLE `cluster_varnishserver` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cluster_vcltemplate`
--

DROP TABLE IF EXISTS `cluster_vcltemplate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cluster_vcltemplate` (
  `id` tinyint(4) DEFAULT NULL,
  `name` varchar(18) DEFAULT NULL,
  `content` varchar(49) DEFAULT NULL,
  `version` decimal(2,1) DEFAULT NULL,
  `comment` varchar(6) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cluster_vcltemplate`
--

LOCK TABLES `cluster_vcltemplate` WRITE;
/*!40000 ALTER TABLE `cluster_vcltemplate` DISABLE KEYS */;
INSERT INTO `cluster_vcltemplate` VALUES (2,'vagrant_template_4','<VCL/>\r\nsub vcl_recv {\r\n    <FLEXIBLE_ROUTER/>\r\n}',4.0,'wefwef');
/*!40000 ALTER TABLE `cluster_vcltemplate` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cluster_vcltemplateblock`
--

DROP TABLE IF EXISTS `cluster_vcltemplateblock`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cluster_vcltemplateblock` (
  `id` varchar(0) DEFAULT NULL,
  `tag` varchar(0) DEFAULT NULL,
  `template_id` varchar(0) DEFAULT NULL,
  `content` varchar(0) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cluster_vcltemplateblock`
--

LOCK TABLES `cluster_vcltemplateblock` WRITE;
/*!40000 ALTER TABLE `cluster_vcltemplateblock` DISABLE KEYS */;
/*!40000 ALTER TABLE `cluster_vcltemplateblock` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cluster_vclvariable`
--

DROP TABLE IF EXISTS `cluster_vclvariable`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cluster_vclvariable` (
  `id` varchar(0) DEFAULT NULL,
  `key` varchar(0) DEFAULT NULL,
  `value` varchar(0) DEFAULT NULL,
  `cluster_id` varchar(0) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cluster_vclvariable`
--

LOCK TABLES `cluster_vclvariable` WRITE;
/*!40000 ALTER TABLE `cluster_vclvariable` DISABLE KEYS */;
/*!40000 ALTER TABLE `cluster_vclvariable` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_admin_log` (
  `id` varchar(0) DEFAULT NULL,
  `object_id` varchar(0) DEFAULT NULL,
  `object_repr` varchar(0) DEFAULT NULL,
  `action_flag` varchar(0) DEFAULT NULL,
  `change_message` varchar(0) DEFAULT NULL,
  `content_type_id` varchar(0) DEFAULT NULL,
  `user_id` varchar(0) DEFAULT NULL,
  `action_time` varchar(0) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_content_type` (
  `id` tinyint(4) DEFAULT NULL,
  `app_label` varchar(13) DEFAULT NULL,
  `model` varchar(26) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'admin','logentry'),(3,'auth','group'),(4,'auth','permission'),(2,'auth','user'),(14,'cluster','dc'),(15,'cluster','historicalvcltemplate'),(18,'cluster','historicalvcltemplateblock'),(13,'cluster','logicalcluster'),(17,'cluster','varnishserver'),(16,'cluster','vcltemplate'),(19,'cluster','vcltemplateblock'),(20,'cluster','vclvariable'),(5,'contenttypes','contenttype'),(12,'manager','backend'),(11,'manager','director'),(9,'manager','probe'),(10,'manager','timeprofile'),(23,'monitor','backendstatus'),(22,'router','positiveurl'),(21,'router','route'),(6,'sessions','session'),(28,'social_django','association'),(26,'social_django','code'),(30,'social_django','nonce'),(27,'social_django','partial'),(29,'social_django','usersocialauth'),(24,'taggit','tag'),(25,'taggit','taggeditem'),(8,'tastypie','apiaccess'),(7,'tastypie','apikey');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_migrations` (
  `id` tinyint(4) DEFAULT NULL,
  `app` varchar(13) DEFAULT NULL,
  `name` varchar(40) DEFAULT NULL,
  `applied` varchar(10) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2020-06-05'),(2,'auth','0001_initial','2020-06-05'),(3,'admin','0001_initial','2020-06-05'),(4,'admin','0002_logentry_remove_auto_add','2020-06-05'),(5,'contenttypes','0002_remove_content_type_name','2020-06-05'),(6,'auth','0002_alter_permission_name_max_length','2020-06-05'),(7,'auth','0003_alter_user_email_max_length','2020-06-05'),(8,'auth','0004_alter_user_username_opts','2020-06-05'),(9,'auth','0005_alter_user_last_login_null','2020-06-05'),(10,'auth','0006_require_contenttypes_0002','2020-06-05'),(11,'auth','0007_alter_validators_add_error_messages','2020-06-05'),(12,'auth','0008_alter_user_username_max_length','2020-06-05'),(13,'sessions','0001_initial','2020-06-05'),(14,'default','0001_initial','2020-06-05'),(15,'social_auth','0001_initial','2020-06-05'),(16,'default','0002_add_related_name','2020-06-05'),(17,'social_auth','0002_add_related_name','2020-06-05'),(18,'default','0003_alter_email_max_length','2020-06-05'),(19,'social_auth','0003_alter_email_max_length','2020-06-05'),(20,'default','0004_auto_20160423_0400','2020-06-05'),(21,'social_auth','0004_auto_20160423_0400','2020-06-05'),(22,'social_auth','0005_auto_20160727_2333','2020-06-05'),(23,'social_django','0006_partial','2020-06-05'),(24,'social_django','0007_code_timestamp','2020-06-05'),(25,'social_django','0008_partial_timestamp','2020-06-05'),(26,'taggit','0001_initial','2020-06-05'),(27,'taggit','0002_auto_20150616_2121','2020-06-05'),(28,'tastypie','0001_initial','2020-06-05'),(29,'social_django','0003_alter_email_max_length','2020-06-05'),(30,'social_django','0002_add_related_name','2020-06-05'),(31,'social_django','0005_auto_20160727_2333','2020-06-05'),(32,'social_django','0001_initial','2020-06-05'),(33,'social_django','0004_auto_20160423_0400','2020-06-05');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_session` (
  `session_key` varchar(0) DEFAULT NULL,
  `session_data` varchar(0) DEFAULT NULL,
  `expire_date` varchar(0) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `manager_backend`
--

DROP TABLE IF EXISTS `manager_backend`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `manager_backend` (
  `id` tinyint(4) DEFAULT NULL,
  `address` varchar(14) DEFAULT NULL,
  `port` tinyint(4) DEFAULT NULL,
  `weight` tinyint(4) DEFAULT NULL,
  `dc_id` tinyint(4) DEFAULT NULL,
  `max_connections` tinyint(4) DEFAULT NULL,
  `connect_timeout` decimal(2,1) DEFAULT NULL,
  `first_byte_timeout` tinyint(4) DEFAULT NULL,
  `between_bytes_timeout` tinyint(4) DEFAULT NULL,
  `director_id` tinyint(4) DEFAULT NULL,
  `enabled` tinyint(4) DEFAULT NULL,
  `inherit_time_profile` tinyint(4) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `manager_backend`
--

LOCK TABLES `manager_backend` WRITE;
/*!40000 ALTER TABLE `manager_backend` DISABLE KEYS */;
INSERT INTO `manager_backend` VALUES (1,'192.168.199.10',80,1,1,5,0.3,5,1,1,1,1),(2,'192.168.199.11',80,1,1,5,0.3,5,1,1,1,1),(3,'192.168.199.12',80,2,1,5,0.3,5,1,1,1,1),(4,'192.168.199.13',80,3,1,5,0.3,5,1,2,1,1),(5,'192.168.199.14',80,4,1,5,0.3,5,1,2,1,1),(6,'192.168.199.15',80,5,1,5,0.3,5,1,2,1,1);
/*!40000 ALTER TABLE `manager_backend` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `manager_director`
--

DROP TABLE IF EXISTS `manager_director`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `manager_director` (
  `id` tinyint(4) DEFAULT NULL,
  `name` varchar(14) DEFAULT NULL,
  `service` varchar(5) DEFAULT NULL,
  `mode` varchar(11) DEFAULT NULL,
  `protocol` varchar(4) DEFAULT NULL,
  `hashing_policy` varchar(7) DEFAULT NULL,
  `router` varchar(13) DEFAULT NULL,
  `route_expression` varchar(8) DEFAULT NULL,
  `active_active` tinyint(4) DEFAULT NULL,
  `probe_id` tinyint(4) DEFAULT NULL,
  `enabled` tinyint(4) DEFAULT NULL,
  `remove_path` tinyint(4) DEFAULT NULL,
  `time_profile_id` tinyint(4) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `manager_director`
--

LOCK TABLES `manager_director` WRITE;
/*!40000 ALTER TABLE `manager_director` DISABLE KEYS */;
INSERT INTO `manager_director` VALUES (1,'first_service','Cart','random','both','req.url','req.url','/first',1,1,1,0,1),(2,'second_service','Order','round-robin','both','req.url','req.http.host','second.*',1,1,1,0,1);
/*!40000 ALTER TABLE `manager_director` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `manager_director_cluster`
--

DROP TABLE IF EXISTS `manager_director_cluster`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `manager_director_cluster` (
  `id` tinyint(4) DEFAULT NULL,
  `director_id` tinyint(4) DEFAULT NULL,
  `logicalcluster_id` tinyint(4) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `manager_director_cluster`
--

LOCK TABLES `manager_director_cluster` WRITE;
/*!40000 ALTER TABLE `manager_director_cluster` DISABLE KEYS */;
INSERT INTO `manager_director_cluster` VALUES (1,1,1),(2,2,1),(3,2,2),(4,2,3),(5,2,4);
/*!40000 ALTER TABLE `manager_director_cluster` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `manager_probe`
--

DROP TABLE IF EXISTS `manager_probe`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `manager_probe` (
  `id` tinyint(4) DEFAULT NULL,
  `name` varchar(13) DEFAULT NULL,
  `url` varchar(5) DEFAULT NULL,
  `expected_response` smallint(6) DEFAULT NULL,
  `interval` tinyint(4) DEFAULT NULL,
  `timeout` tinyint(4) DEFAULT NULL,
  `window` tinyint(4) DEFAULT NULL,
  `threshold` tinyint(4) DEFAULT NULL,
  `start_as_healthy` tinyint(4) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `manager_probe`
--

LOCK TABLES `manager_probe` WRITE;
/*!40000 ALTER TABLE `manager_probe` DISABLE KEYS */;
INSERT INTO `manager_probe` VALUES (1,'default_probe','/ts.1',200,3,1,5,3,0);
/*!40000 ALTER TABLE `manager_probe` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `manager_timeprofile`
--

DROP TABLE IF EXISTS `manager_timeprofile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `manager_timeprofile` (
  `id` tinyint(4) DEFAULT NULL,
  `name` varchar(15) DEFAULT NULL,
  `description` varchar(0) DEFAULT NULL,
  `max_connections` tinyint(4) DEFAULT NULL,
  `connect_timeout` decimal(2,1) DEFAULT NULL,
  `first_byte_timeout` tinyint(4) DEFAULT NULL,
  `between_bytes_timeout` tinyint(4) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `manager_timeprofile`
--

LOCK TABLES `manager_timeprofile` WRITE;
/*!40000 ALTER TABLE `manager_timeprofile` DISABLE KEYS */;
INSERT INTO `manager_timeprofile` VALUES (1,'generic profile','',5,0.3,5,1);
/*!40000 ALTER TABLE `manager_timeprofile` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `monitor_backendstatus`
--

DROP TABLE IF EXISTS `monitor_backendstatus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `monitor_backendstatus` (
  `id` varchar(0) DEFAULT NULL,
  `address` varchar(0) DEFAULT NULL,
  `port` varchar(0) DEFAULT NULL,
  `timestamp` varchar(0) DEFAULT NULL,
  `status` varchar(0) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `monitor_backendstatus`
--

LOCK TABLES `monitor_backendstatus` WRITE;
/*!40000 ALTER TABLE `monitor_backendstatus` DISABLE KEYS */;
/*!40000 ALTER TABLE `monitor_backendstatus` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `router_positiveurl`
--

DROP TABLE IF EXISTS `router_positiveurl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `router_positiveurl` (
  `id` varchar(0) DEFAULT NULL,
  `url` varchar(0) DEFAULT NULL,
  `route_id` varchar(0) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `router_positiveurl`
--

LOCK TABLES `router_positiveurl` WRITE;
/*!40000 ALTER TABLE `router_positiveurl` DISABLE KEYS */;
/*!40000 ALTER TABLE `router_positiveurl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `router_route`
--

DROP TABLE IF EXISTS `router_route`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `router_route` (
  `id` tinyint(4) DEFAULT NULL,
  `condition` varchar(25) DEFAULT NULL,
  `priority` tinyint(4) DEFAULT NULL,
  `director_id` tinyint(4) DEFAULT NULL,
  `action` varchar(4) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `router_route`
--

LOCK TABLES `router_route` WRITE;
/*!40000 ALTER TABLE `router_route` DISABLE KEYS */;
INSERT INTO `router_route` VALUES (1,'req.url ~ \"^/flexibleee\"',51,2,'pass');
/*!40000 ALTER TABLE `router_route` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `router_route_clusters`
--

DROP TABLE IF EXISTS `router_route_clusters`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `router_route_clusters` (
  `id` tinyint(4) DEFAULT NULL,
  `route_id` tinyint(4) DEFAULT NULL,
  `logicalcluster_id` tinyint(4) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `router_route_clusters`
--

LOCK TABLES `router_route_clusters` WRITE;
/*!40000 ALTER TABLE `router_route_clusters` DISABLE KEYS */;
INSERT INTO `router_route_clusters` VALUES (1,1,4);
/*!40000 ALTER TABLE `router_route_clusters` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `social_auth_association`
--

DROP TABLE IF EXISTS `social_auth_association`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `social_auth_association` (
  `id` varchar(0) DEFAULT NULL,
  `server_url` varchar(0) DEFAULT NULL,
  `handle` varchar(0) DEFAULT NULL,
  `secret` varchar(0) DEFAULT NULL,
  `issued` varchar(0) DEFAULT NULL,
  `lifetime` varchar(0) DEFAULT NULL,
  `assoc_type` varchar(0) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `social_auth_association`
--

LOCK TABLES `social_auth_association` WRITE;
/*!40000 ALTER TABLE `social_auth_association` DISABLE KEYS */;
/*!40000 ALTER TABLE `social_auth_association` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `social_auth_code`
--

DROP TABLE IF EXISTS `social_auth_code`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `social_auth_code` (
  `id` varchar(0) DEFAULT NULL,
  `email` varchar(0) DEFAULT NULL,
  `code` varchar(0) DEFAULT NULL,
  `verified` varchar(0) DEFAULT NULL,
  `timestamp` varchar(0) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `social_auth_code`
--

LOCK TABLES `social_auth_code` WRITE;
/*!40000 ALTER TABLE `social_auth_code` DISABLE KEYS */;
/*!40000 ALTER TABLE `social_auth_code` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `social_auth_nonce`
--

DROP TABLE IF EXISTS `social_auth_nonce`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `social_auth_nonce` (
  `id` varchar(0) DEFAULT NULL,
  `server_url` varchar(0) DEFAULT NULL,
  `timestamp` varchar(0) DEFAULT NULL,
  `salt` varchar(0) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `social_auth_nonce`
--

LOCK TABLES `social_auth_nonce` WRITE;
/*!40000 ALTER TABLE `social_auth_nonce` DISABLE KEYS */;
/*!40000 ALTER TABLE `social_auth_nonce` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `social_auth_partial`
--

DROP TABLE IF EXISTS `social_auth_partial`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `social_auth_partial` (
  `id` varchar(0) DEFAULT NULL,
  `token` varchar(0) DEFAULT NULL,
  `next_step` varchar(0) DEFAULT NULL,
  `backend` varchar(0) DEFAULT NULL,
  `data` varchar(0) DEFAULT NULL,
  `timestamp` varchar(0) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `social_auth_partial`
--

LOCK TABLES `social_auth_partial` WRITE;
/*!40000 ALTER TABLE `social_auth_partial` DISABLE KEYS */;
/*!40000 ALTER TABLE `social_auth_partial` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `social_auth_usersocialauth`
--

DROP TABLE IF EXISTS `social_auth_usersocialauth`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `social_auth_usersocialauth` (
  `id` varchar(0) DEFAULT NULL,
  `provider` varchar(0) DEFAULT NULL,
  `uid` varchar(0) DEFAULT NULL,
  `user_id` varchar(0) DEFAULT NULL,
  `extra_data` varchar(0) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `social_auth_usersocialauth`
--

LOCK TABLES `social_auth_usersocialauth` WRITE;
/*!40000 ALTER TABLE `social_auth_usersocialauth` DISABLE KEYS */;
/*!40000 ALTER TABLE `social_auth_usersocialauth` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sqlite_sequence`
--

DROP TABLE IF EXISTS `sqlite_sequence`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sqlite_sequence` (
  `name` varchar(26) DEFAULT NULL,
  `seq` tinyint(4) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sqlite_sequence`
--

LOCK TABLES `sqlite_sequence` WRITE;
/*!40000 ALTER TABLE `sqlite_sequence` DISABLE KEYS */;
INSERT INTO `sqlite_sequence` VALUES ('django_migrations',33),('django_admin_log',0),('django_content_type',30),('auth_permission',90),('auth_user',1),('social_auth_usersocialauth',0),('social_auth_code',0),('social_auth_partial',0),('manager_timeprofile',1),('manager_probe',1),('manager_director',2),('manager_director_cluster',5),('cluster_dc',2),('manager_backend',6),('cluster_logicalcluster',4),('cluster_vcltemplate',2),('cluster_varnishserver',4),('router_route',1),('router_route_clusters',1);
/*!40000 ALTER TABLE `sqlite_sequence` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `taggit_tag`
--

DROP TABLE IF EXISTS `taggit_tag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `taggit_tag` (
  `id` varchar(0) DEFAULT NULL,
  `name` varchar(0) DEFAULT NULL,
  `slug` varchar(0) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `taggit_tag`
--

LOCK TABLES `taggit_tag` WRITE;
/*!40000 ALTER TABLE `taggit_tag` DISABLE KEYS */;
/*!40000 ALTER TABLE `taggit_tag` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `taggit_taggeditem`
--

DROP TABLE IF EXISTS `taggit_taggeditem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `taggit_taggeditem` (
  `id` varchar(0) DEFAULT NULL,
  `object_id` varchar(0) DEFAULT NULL,
  `content_type_id` varchar(0) DEFAULT NULL,
  `tag_id` varchar(0) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `taggit_taggeditem`
--

LOCK TABLES `taggit_taggeditem` WRITE;
/*!40000 ALTER TABLE `taggit_taggeditem` DISABLE KEYS */;
/*!40000 ALTER TABLE `taggit_taggeditem` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tastypie_apiaccess`
--

DROP TABLE IF EXISTS `tastypie_apiaccess`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tastypie_apiaccess` (
  `id` varchar(0) DEFAULT NULL,
  `identifier` varchar(0) DEFAULT NULL,
  `url` varchar(0) DEFAULT NULL,
  `request_method` varchar(0) DEFAULT NULL,
  `accessed` varchar(0) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tastypie_apiaccess`
--

LOCK TABLES `tastypie_apiaccess` WRITE;
/*!40000 ALTER TABLE `tastypie_apiaccess` DISABLE KEYS */;
/*!40000 ALTER TABLE `tastypie_apiaccess` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tastypie_apikey`
--

DROP TABLE IF EXISTS `tastypie_apikey`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tastypie_apikey` (
  `id` varchar(0) DEFAULT NULL,
  `key` varchar(0) DEFAULT NULL,
  `created` varchar(0) DEFAULT NULL,
  `user_id` varchar(0) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tastypie_apikey`
--

LOCK TABLES `tastypie_apikey` WRITE;
/*!40000 ALTER TABLE `tastypie_apikey` DISABLE KEYS */;
/*!40000 ALTER TABLE `tastypie_apikey` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2019-08-22 15:20:35
