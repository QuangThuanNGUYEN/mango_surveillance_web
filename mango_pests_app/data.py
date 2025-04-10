# Created a file for the data 
from .mango_threat import MangoThreat

# mango_pests_app/data.py


# List of MangoThreat instances
# List of MangoThreat instances with threat_type
mango_threats = [
    MangoThreat(name='Anthracnose', slug='anthracnose', description='Description of threat 1', image='Anthracnose.png', details='Full details of Anthracnose', threat_type='Disease'),
    MangoThreat(name='Bacterial Black Spot', slug='bacterial-black-spot', description='Description of threat 2', image='bacterialblackspot.png', details='Full details of Bacterial Black Spot', threat_type='Disease'),
    MangoThreat(name='Mango Scab', slug='mango-scab', description='Description of threat 3', image='mangoscab.png', details='Full details of Mango Scab', threat_type='Disease'),
    MangoThreat(name='Mango Scale', slug='mango-scale', description='Description of threat 4', image='mangoscale.png', details='Full details of Mango Scale', threat_type='Pest'),
    MangoThreat(name='Fruit Fly', slug='fruit-fly', description='Description of threat 5', image='fruitfly.png', details='Full details of Fruit Fly', threat_type='Pest'),
    MangoThreat(name='Mango Leafhoppers', slug='mango-leafhoppers', description='Description of threat 6', image='mangoleafhopper.png', details='Full details of Mango Leafhoppers', threat_type='Pest'),
    MangoThreat(name='Mango Seed Weevil', slug='mango-seed-weevil', description='Description of threat 7', image='seedweevil.png', details='Full details of Mango Seed Weevil', threat_type='Pest')
]


