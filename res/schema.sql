create table users (
  ID integer key auto_increment not null,
  NAME varchar(32) not null
);

create table ladders (
  ID integer key auto_increment not null,
  NAME varchar(32) not null,
  START_DATE date not null,
  END_DATE date not null
);

create table scores (
  USER_ID integer not null,
  LADDER_ID integer not null,
  SCORE integer not null default 0,
  primary key (USER_ID, LADDER_ID),
  foreign key (USER_ID) references users(ID) on delete cascade,
  foreign key (LADDER_ID) references ladders(ID) on delete cascade
);

create table matches(
  ID integer key auto_increment not null,
  WINNER_ID integer not null,
  LOSER_ID integer not null,
  WINNER_SET1_SCORE integer not null,
  LOSER_SET1_SCORE integer not null,
  WINNER_SET2_SCORE integer not null,
  LOSER_SET2_SCORE integer not null,
  WINNER_SET3_SCORE integer,
  LOSER_SET3_SCORE integer,
  foreign key (WINNER_ID) references users(ID) on delete cascade,
  foreign key (LOSER_ID) references users(ID) on delete cascade
);