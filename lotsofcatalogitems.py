from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import csv

from database_setup import Category, Base, Item, User


engine = create_engine('postgresql://catalog:2018catitem@localhost/catalogitems')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations
# with the database and represents a "staging zone" for
# all the objects loaded into the database session object.
# Any change made against the objects in the session
# won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes,
# you can revert all of them back to the last commit by
# calling session.rollback()
session = DBSession()

# SET client_encoding TO 'UTF-8'

# Users creation
with open('user.csv', 'r') as user_file:

    user_dict = csv.DictReader(user_file)

    for u in user_dict:
        print(u)

        userc = User(name=u['name'], email=u['email'],
                    picture=u['picture'])

        session.add(userc)
        session.commit()

# Categories Creation
with open('category.csv', 'r') as category_file:

    category_dict = csv.DictReader(category_file)
    for c in category_dict:

        category = Category(name=c['name'],
                            user_id=c['user_id'])

        session.add(category)
        session.commit()

# Items creation
with open('item.csv', 'r') as item_file:

    item_dict = csv.DictReader(item_file)

    for it in item_dict:
        
        item = Item(name=it['name'],
                    description=buffer(it['description']),
                    picture=it['picture'],
                    price=it['price'],
                    category_id=(it['category_id']),
                    user_id=(it['user_id']))
        # print(it['category_id'])
        # print(it['user_id'])
        session.add(item)
        session.commit()


print("All data loaded !!")
