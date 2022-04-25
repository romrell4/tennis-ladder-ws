# drop table users;
create table users (
  ID varchar(64) key not null,
  NAME varchar(64) not null,
  EMAIL varchar(64) not null,
  PHONE_NUMBER varchar(32),
  PHOTO_URL varchar(256),
  AVAILABILITY_TEXT varchar(512)
);

# drop table ladders;
CREATE TABLE `ladders` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `NAME` varchar(32) NOT NULL,
  `START_DATE` date NOT NULL,
  `END_DATE` date NOT NULL,
  `DISTANCE_PENALTY_ON` tinyint(1) NOT NULL DEFAULT '0',
  `WEEKS_FOR_BORROWED_POINTS` smallint(6) NOT NULL DEFAULT '0',
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=latin1;

# drop table players;
CREATE TABLE `players` (
  `USER_ID` varchar(64) NOT NULL,
  `LADDER_ID` int(11) NOT NULL,
  `EARNED_POINTS` smallint(6) NOT NULL DEFAULT '0',
  `BORROWED_POINTS` smallint(6) NOT NULL DEFAULT '0',
  `ORDER` smallint(6) NOT NULL DEFAULT '0',
  PRIMARY KEY (`USER_ID`,`LADDER_ID`),
  KEY `LADDER_ID` (`LADDER_ID`),
  CONSTRAINT `players_ibfk_1` FOREIGN KEY (`USER_ID`) REFERENCES `users` (`ID`) ON DELETE CASCADE,
  CONSTRAINT `players_ibfk_2` FOREIGN KEY (`LADDER_ID`) REFERENCES `ladders` (`ID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

# drop table matches;
create table matches(
  ID integer key auto_increment not null,
  LADDER_ID integer not null,
  MATCH_DATE datetime not null,
  WINNER_ID varchar(64) not null,
  LOSER_ID varchar(64) not null,
  WINNER_SET1_SCORE integer not null,
  LOSER_SET1_SCORE integer not null,
  WINNER_SET2_SCORE integer not null,
  LOSER_SET2_SCORE integer not null,
  WINNER_SET3_SCORE integer,
  LOSER_SET3_SCORE integer,
  foreign key (LADDER_ID) references ladders(ID) on delete cascade,
  foreign key (WINNER_ID) references users(ID) on delete cascade,
  foreign key (LOSER_ID) references users(ID) on delete cascade
);

# drop table ladder_codes;
create table ladder_codes(
  LADDER_ID integer key not null,
  CODE varchar(64) not null,
  foreign key (LADDER_ID) references ladders(ID) on delete cascade
)