-- Sample Craigslist locations for testing
-- This script can be run after the database is set up to populate initial locations

INSERT INTO locations (name, code, url, state, country, is_active) VALUES
-- California
('San Francisco Bay Area', 'sfbay', 'https://sfbay.craigslist.org', 'California', 'US', true),
('Los Angeles', 'losangeles', 'https://losangeles.craigslist.org', 'California', 'US', true),
('San Diego', 'sandiego', 'https://sandiego.craigslist.org', 'California', 'US', true),
('Sacramento', 'sacramento', 'https://sacramento.craigslist.org', 'California', 'US', true),

-- New York
('New York City', 'newyork', 'https://newyork.craigslist.org', 'New York', 'US', true),
('Albany', 'albany', 'https://albany.craigslist.org', 'New York', 'US', true),
('Buffalo', 'buffalo', 'https://buffalo.craigslist.org', 'New York', 'US', true),

-- Texas
('Houston', 'houston', 'https://houston.craigslist.org', 'Texas', 'US', true),
('Dallas', 'dallas', 'https://dallas.craigslist.org', 'Texas', 'US', true),
('Austin', 'austin', 'https://austin.craigslist.org', 'Texas', 'US', true),
('San Antonio', 'sanantonio', 'https://sanantonio.craigslist.org', 'Texas', 'US', true),

-- Florida
('Miami', 'miami', 'https://miami.craigslist.org', 'Florida', 'US', true),
('Orlando', 'orlando', 'https://orlando.craigslist.org', 'Florida', 'US', true),
('Tampa Bay', 'tampa', 'https://tampa.craigslist.org', 'Florida', 'US', true),

-- Illinois
('Chicago', 'chicago', 'https://chicago.craigslist.org', 'Illinois', 'US', true),

-- Washington
('Seattle', 'seattle', 'https://seattle.craigslist.org', 'Washington', 'US', true),

-- Colorado
('Denver', 'denver', 'https://denver.craigslist.org', 'Colorado', 'US', true),

-- Arizona
('Phoenix', 'phoenix', 'https://phoenix.craigslist.org', 'Arizona', 'US', true),

-- Nevada
('Las Vegas', 'lasvegas', 'https://lasvegas.craigslist.org', 'Nevada', 'US', true),

-- Oregon
('Portland', 'portland', 'https://portland.craigslist.org', 'Oregon', 'US', true),

-- Massachusetts
('Boston', 'boston', 'https://boston.craigslist.org', 'Massachusetts', 'US', true)

ON CONFLICT (code) DO NOTHING;