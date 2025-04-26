from usery.models.user import User
from usery.models.tag import Tag
from usery.models.user_tag import UserTag
from usery.models.attribute import Attribute
from usery.models.user_attribute import UserAttribute
from usery.db.session import Base, engine

# Print the models
print("User model:", User.__table__)
print("Tag model:", Tag.__table__)
print("UserTag model:", UserTag.__table__)
print("Attribute model:", Attribute.__table__)
print("UserAttribute model:", UserAttribute.__table__)

print("All models loaded successfully!")