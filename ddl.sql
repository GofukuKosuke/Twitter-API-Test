CREATE TABLE `favorites` (
  `user_id_str` varchar(32) NOT NULL,
  `tweet_id_str` varchar(32) NOT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`user_id_str`,`tweet_id_str`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `my_tweets` (
  `id_str` varchar(32) NOT NULL,
  `created_at` datetime NOT NULL,
  `text` varchar(1024) NOT NULL,
  PRIMARY KEY (`id_str`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `retweets` (
  `user_id_str` varchar(32) NOT NULL,
  `tweet_id_str` varchar(32) NOT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`user_id_str`,`tweet_id_str`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `twitter_users` (
  `id_str` varchar(32) NOT NULL,
  `screen_name` varchar(64) NOT NULL,
  `name` varchar(128) NOT NULL,
  PRIMARY KEY (`id_str`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `replies` (
  `tweet_id_str` varchar(32) NOT NULL,
  `user_id_str` varchar(32) NOT NULL,
  `original_tweet_id_str` varchar(32) NOT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`tweet_id_str`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
