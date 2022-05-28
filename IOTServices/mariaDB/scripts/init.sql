CREATE TABLE device_state (
    id MEDIUMINT NOT NULL AUTO_INCREMENT,
    room varchar(10) NOT NULL,
    type varchar(20) NOT NULL,
    value TINYINT NOT NULL,
    date DATETIME NOT NULL,
    PRIMARY KEY (id)
);
