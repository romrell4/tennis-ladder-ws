# drop table users;
create table users (
  ID varchar(64) key not null,
  NAME varchar(64) not null,
  EMAIL varchar(64) not null,
  PHONE_NUMBER varchar(32),
  PHOTO_URL varchar(256) not null
);

# drop table ladders;
create table ladders (
  ID integer key auto_increment not null,
  NAME varchar(32) not null,
  START_DATE date not null,
  END_DATE date not null
);

# drop table players;
create table players (
  USER_ID varchar(64) not null,
  LADDER_ID integer not null,
  SCORE integer not null default 0,
  primary key (USER_ID, LADDER_ID),
  foreign key (USER_ID) references users(ID) on delete cascade,
  foreign key (LADDER_ID) references ladders(ID) on delete cascade
);

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