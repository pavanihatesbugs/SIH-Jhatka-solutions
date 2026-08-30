CREATE TABLE aadhaar (
aadhaar_id VARCHAR(12) PRIMARY KEY,
name VARCHAR(150),
dob DATE,
gender VARCHAR(20),
vid VARCHAR(50)
);


INSERT INTO aadhaar (aadhaar_id, name, dob, gender, vid)
VALUES
	('123456789101','Basant Raj','2000-01-01' ,'MALE' ,'9110044586690808'),
	('687006240742','Sukumar Karuppiah','1978-05-01','MALE','9181803855623212'),
	('590554540961','Cheruku Sree Chaitra','2008-07-25','FEMALE','9103547731037556'),
	('456789012345','Pavani Praveen','2007-05-25','FEMALE',''),
	('498714770290','Poornima V','2007-07-20','FEMALE',''),
	('935349568480','Tanuja Thakur','2007-02-08','FEMALE','9107076376956206'),
	('893831116226','Darakhshan Parween Zeeshan Shaikh','1997-02-25','FEMALE','9187647016408093'),
	('687006240742','Sukumar Karuppiah','1978-05-01','MALE','9181803855623212');

CREATE TABLE pan (
pan_num VARCHAR(12) PRIMARY KEY,
name VARCHAR(150),
fathers_name VARCHAR(150),
dob DATE

);


INSERT INTO pan (pan_num, name, fathers_name,dob)
VALUES
	('CXXPT5126J', 'TANUJA THAKUR', 'BAL KISHORE THAKUR', '2007-02-08'),
    ('IUWPP1391B', 'PAVANI PRAVEEN', 'PRAVEEN SUBBANANJAPPA', '2007-05-25'),
    ('DBXPC5982E', 'CHERUKU SREE CHAITRA', 'CHERUKU SANTOSH KUMAR', '2008-07-25'),
    ('AEUPC1567N', 'CHERUKU SANTOSH KUMAR', 'NARSING RAO CHERUKU', '1977-10-10'),
    ('DCCPV3843M', 'POORNIMA V', 'VEERESH', '2007-07-20');
	

CREATE TABLE passport (
passport_num VARCHAR(8) PRIMARY KEY,
ptype VARCHAR(1),
country_code VARCHAR(5),
surname VARCHAR(100),
name VARCHAR(100),
nationality VARCHAR(20),
gender VARCHAR(1),
dob DATE,
pob VARCHAR(25),
placeOfIssue VARCHAR(25),
dateOfIssue DATE,
dateOfExpiry DATE


);

INSERT INTO passport (passport_num,ptype,country_code,surname, name,nationality,gender,dob,pob,placeOfIssue,dateOfIssue,dateOfExpiry)
VALUES
	 (
    'J2452409',
    'P',
    'IND',
    'KAUSHAL',
    'SUKHDEEP',
    'IND',
    'F',
    '1991-10-20',
    'GALI KALAN',
    'CHANDIGARH',
    '2010-08-31',
    '2020-08-30'
),
	 (
    'N7820370',
    'P',
    'IND',
    'KALUVA',
    'SANTHOSHI',
    'IND',
    'F',
    '1993-07-09',
    'HYDERABAD, TELANGANA',
    'HYDERABAD',
    '2016-02-15',
    '2026-02-14'
),
	 (
    'M9104700',
    'P',
    'IND',
    'SANDHU',
    'GAGANDEEP SINGH',
    'IND',
    'M',
    '1997-02-01',
    'GANGOHAR, PUNJAB',
    'CHANDIGARH',
    '2015-05-22',
    '2025-05-21'
),
	 (
    'J1440791',
    'P',
    'IND',
    'KAHLON',
    'GURVIR SINGH',
    'IND',
    'M',
    '1990-07-19',
    'MACHHIWARA',
    'CHANDIGARH',
    '2010-07-22',
    '2020-07-21'
),
	 (
    'R7123405',
    'P',
    'IND',
	'',
    'MAQDOOMA FATHIMA',
    'IND',
    'F',
    '1981-06-23',
    'CHENNAI, TAMIL NADU',
    'BENGALURU',
    '2017-12-15',
    '2027-12-14'
),
(
	'H91379927',
	'P',
	'IND',
	'ALAM',
	'MAQSOOD',
	'IND',
	'M',
	'1973-08-14',
	'MUZAFFARPUR BIHAR',
	'DELHI',
	'2010-02-18',
	'2020-02-17'
),
(
	'J7335300',
	'P',
	'IND',
	'',
	'JASPREET KAUR',
	'IND',
	'F',
	'1994-09-24',
	'RAIKOT, PUNJAB',
	'CHANDIGARH',
	'2011-05-24',
	'2021-05-23'
	
);
	