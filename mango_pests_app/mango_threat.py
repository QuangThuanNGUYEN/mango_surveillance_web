class MangoThreat:
    def __init__(self, name, slug, description, image, details, threat_type):
        self.name = name
        self.slug = slug
        self.description = description
        self.image = image
        self.details = details
        self.threat_type = threat_type
        
        
    def __repr__(self):
        return f"Mango Threat (name: {self.name}, threat type: {self.threat_type})"
    
    def get_summary(self):
        return f"{self.name}: {self.decription[:100]}..."
    

