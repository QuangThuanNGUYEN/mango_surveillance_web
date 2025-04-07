# Created a file for the data 
from .mango_threat import MangoThreat

# mango_pests_app/data.py


# List of MangoThreat instances
# List of MangoThreat instances with threat_type

#Ben Note to self: update description= "Description of Project #" with appropriate information.
mango_threats = [
    MangoThreat(name='Anthracnose', slug='anthracnose', description='Anthracnose is a group of fungal diseases that affect a wide variety of plants, causing dark, sunken lesions on leaves, stems, flowers, or fruits. It thrives in warm, wet conditions and spreads through water, wind, or contaminated tools. Proper sanitation, resistant plant varieties, and fungicide application can help manage and prevent its spread.', image='Anthracnose.png', details='Full details of Anthracnose', threat_type='Disease'),
    MangoThreat(name='Bacterial Black Spot', slug='bacterial-black-spot', description='Bacterial Black Spot is a plant disease caused by the bacterium Xanthomonas campestris, commonly affecting roses and some vegetable crops. It presents as black or dark brown spots with yellow halos on leaves, eventually leading to leaf drop and weakened plant health. The disease spreads through water splashes, wind, or infected tools, and is best managed through proper pruning, sanitation, and resistant plant varieties.', image='bacterialblackspot.png', details='Full details of Bacterial Black Spot', threat_type='Disease'),
    MangoThreat(name='Mango Scab', slug='mango-scab', description='Mango Scab is a fungal disease caused by Elsinoë mangiferae that leads to dark, scabby lesions on young leaves, twigs, and fruit. It can reduce fruit quality and marketability if not controlled early. Good airflow, sanitation, and fungicide sprays help manage the disease.', image='mangoscab.png', details='Full details of Mango Scab', threat_type='Disease'),
    MangoThreat(name='Mango Scale', slug='mango-scale', description='Mango Scale refers to small, sap-sucking insects that attach to mango tree bark, leaves, and fruit, weakening the plant. Heavy infestations can lead to yellowing leaves, premature fruit drop, and reduced yields. They can be controlled with horticultural oils, beneficial insects, or systemic insecticides.', image='mangoscale.png', details='Full details of Mango Scale', threat_type='Pest'),
    MangoThreat(name='Fruit Fly', slug='fruit-fly', description='Fruit flies are major mango pests whose larvae burrow into ripening fruit, causing it to rot from the inside. Infestation makes the fruit unmarketable and leads to significant crop loss. Traps, sanitation, and timely harvesting are effective control strategies.', image='fruitfly.png', details='Full details of Fruit Fly', threat_type='Pest'),
    MangoThreat(name='Mango Leafhoppers', slug='mango-leafhoppers', description='Mango Leafhoppers are small, jumping insects that feed on mango sap and excrete honeydew, promoting sooty mold growth. They are especially damaging during flowering, as they reduce fruit set. Management includes pruning, insecticides, and controlling their populations early in the season.', image='mangoleafhopper.png', details='Full details of Mango Leafhoppers', threat_type='Pest'),
    MangoThreat(name='Mango Seed Weevil', slug='mango-seed-weevil', description='The Mango Seed Weevil (Sternochetus mangiferae) is a hidden pest that lays eggs on developing mango fruit, with larvae tunneling into the seed. Though it doesn’t damage the fruit externally, it renders the seed useless and is a quarantine concern. Sanitation and monitoring are key to preventing its spread.', image='seedweevil.png', details='Full details of Mango Seed Weevil', threat_type='Pest')
]


