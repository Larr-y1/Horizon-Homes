#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Property, UserProperty, Review

# ------------------------- Authentication -------------------------
class Users(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {"error": "Unauthorized"}, 401

        user = User.query.get(user_id)
        if not user:
            return {"error": "User not found"}, 404

        return {user.to_dict()}, 200


class Signup(Resource):
    def post(self):
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role=""  # role chosen later

        if not name or not email or not password :
            return {'message': 'Email, password are required.'}, 400

        try:
            new_user = User(name=name, email=email, role=role)
            new_user.password_hash = password  

            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = new_user.id  

            return {'message': 'User created successfully.',
            'user':{
                'id': new_user.id,
                'email': new_user.email,
                'role': new_user.role }
            }, 201

        except IntegrityError:
            return {'error': 'User with this email already exists.'}, 409


class Login(Resource):
    def post(self):

        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        role = data.get('role') 

        if not email or not password:
            return {'message': 'Email and password are required.'}, 400

        user = User.query.filter_by(email=email).first()

        if user and user.authenticate(password):
            session['user_id'] = user.id  
            return {'message': 'Login successful.',
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'role': user.role
                    }}, 200
        else:
            return {'error': 'Invalid email or password.'}, 401

class SessionCheck(Resource):
    def get(self):
        user_id = session.get('user_id')
        role = session.get('role')

        if user_id:
            user = User.query.get(user_id)
            if user:
                return {
                    'message': 'User is logged in.',
                    'user_id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'role': user.role
                }, 200
            else:
                return {'message': 'User not found.'}, 404
        else:
            return {'message': 'Unauthorized'}, 401


class Logout(Resource):
    def delete(self):
        session.clear()
        return {}, 204


class SessionCheck(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            return user.to_dict(rules=('-user_properties',)), 200
        return {}, 401


# ------------------------- Role Setting -------------------------
class SetRole(Resource):
    def patch(self, user_id):
        data = request.get_json()
        user = User.query.get(user_id)
        if user:
            user.role = data.get("role")
            db.session.commit()
            return user.to_dict(rules=('-user_properties',)), 200
        return {"error": "User not found"}, 404


# ------------------------- Properties -------------------------
class PropertyList(Resource):
    def get(self):
        # user_id = session.get('user_id')
        # if not user_id:
        #     return {"error": "Unauthorized access. Please log in."}, 401
        
        homes = Property.query.all()
        home_list = []
        for home in homes:
            home_list.append(home.to_dict(rules=('-user_properties',)))
        return home_list, 200

    def post(self):
        data = request.get_json()

        title = data.get('title')
        location = data.get('location')
        image_url = data.get('image_url')
        bedrooms = data.get('bedrooms')
        size = data.get('size')
        distance = data.get('distance')
        price = data.get('price')
        type = data.get('type')
        description = data.get('description')
        features = data.get('features')

        if not title or not location or not price:
            return {"error": "Title, location and price are required."}, 400
        
        # Get logged-in user (owner)
        user_id = session.get('user_id')
        if not user_id:
            return {"error": "User not authenticated."}, 401

        new_home = Property(
            title=title,
            location=location,
            image_url=image_url,
            bedrooms=bedrooms,
            size=size,
            distance=distance,
            price=price,
            type=type,
            description=description,
            features=features
        )
        db.session.add(new_home)
        db.session.commit()
        
        user_property = UserProperty(user_id=user_id, property_id=new_home.id)
        db.session.add(user_property)
        db.session.commit()

        return new_home.to_dict(rules=('-user_properties',)), 201


class PropertyByID(Resource):
    def get(self, property_id):
        home = Property.query.get(property_id)
        if not home:
            return {"error": "Home not found."}, 404
        return home.to_dict(rules=('-user_properties',)), 200
    def patch(self, property_id):
        home = Property.query.get(property_id)

        if not home:
            return {"error": "Home not found."}, 404

        data = request.get_json()

        if 'title' in data:
            home.title = data['title']
        if 'location' in data:
            home.location = data['location']
        if 'image_url' in data:
            home.image_url = data['image_url']
        if 'bedrooms' in data:
            home.bedrooms = data['bedrooms']
        if 'size' in data:
            home.size = data['size']
        if 'distance' in data:
            home.distance = data['distance']
        if 'price' in data:
            home.price = data['price']
        if 'type' in data:
            home.type = data['type']
        if 'description' in data:
            home.description = data['description']
        if 'features' in data:
            home.features = data['features']

        db.session.commit()

        return home.to_dict(rules=('-user_properties',)), 200

    def delete(self, property_id):
        home = Property.query.get(property_id)

        if not home:
            return {"error": "Home not found."}, 404

        db.session.delete(home)
        db.session.commit()

        return {"message": "Home deleted successfully."}, 200

class OwnerProperties(Resource):
    
    def get(self, user_id):
        user = User.query.get(user_id)
        if not user:
            return {'message': 'User not found.'}, 404

        properties = [up.property.to_dict() for up in user.user_properties]
        return properties, 200



# ------------------------- Reviews -------------------------
class Reviews(Resource):
    def post(self):
        user_id = session.get('user_id')
        if not user_id:
            return {"error": "User not authenticated."}, 401

        data = request.get_json()
        property_id = data.get('property_id')
        comments = data.get('comments')
        ratings = data.get('ratings')

        if not property_id or not ratings:
            return {"error": "Property ID and ratings are required."}, 400


        property_obj = Property.query.get(property_id)
        if not property_obj:
            return {"error": "Property not found."}, 404


        user_property = UserProperty.query.filter_by(
            user_id=user_id, 
            property_id=property_id
        ).first()

        if not user_property:
            user_property = UserProperty(
                user_id=user_id, 
                property_id=property_id,
                relationship_type='interested'
            )
            db.session.add(user_property)
            db.session.commit()

        existing_review = Review.query.filter_by(user_property_id=user_property.id).first()
        if existing_review:
            return {"error": "You have already reviewed this property."}, 409

        try:
            new_review = Review(
                comments=comments,
                ratings=ratings,
                user_property_id=user_property.id
            )
            
            db.session.add(new_review)
            db.session.commit()

            return {
                "message": "Review created successfully.",
                "review": {
                    "id": new_review.id,
                    "comments": new_review.comments,
                    "ratings": new_review.ratings,
                    "created_at": new_review.created_at.isoformat(),
                    "property_id": property_id,
                    "reviewer_name": user_property.user.name
                }
            }, 201

        except ValueError as e:
            return {"error": str(e)}, 400
        except Exception as e:
            db.session.rollback()
            return {"error": "Failed to create review."}, 500


class PropertyReviews(Resource):
    def get(self, property_id):
        property_obj = Property.query.get(property_id)
        if not property_obj:
            return {"error": "Property not found."}, 404


        reviews = []
        for user_property in property_obj.user_properties:
            for review in user_property.reviews:
                reviews.append({
                    "id": review.id,
                    "comments": review.comments,
                    "ratings": review.ratings,
                    "created_at": review.created_at.isoformat(),
                    "updated_at": review.updated_at.isoformat() if hasattr(review, 'updated_at') else None,
                    "reviewer_name": user_property.user.name,
                    "reviewer_id": user_property.user.id
                })

        if reviews:
            average_rating = sum(review['ratings'] for review in reviews) / len(reviews)
            average_rating = round(average_rating, 1)
        else:
            average_rating = 0

        return {
            "property_id": property_id,
            "property_title": property_obj.title,
            "total_reviews": len(reviews),
            "average_rating": average_rating,
            "reviews": reviews
        }, 200


# ------------------------- Registerd Resources -------------------------
api.add_resource(Users, '/users')
api.add_resource(Signup, '/signup')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(SessionCheck, '/check_session')
api.add_resource(SetRole, '/set_role/<int:user_id>')

api.add_resource(PropertyList, '/properties')
api.add_resource(PropertyByID, '/properties/<int:property_id>')
api.add_resource(OwnerProperties, '/owner/<int:user_id>/properties')

api.add_resource(Reviews, '/reviews')
api.add_resource(PropertyReviews, '/properties/<int:property_id>/reviews')

if __name__ == '__main__':
    app.run(port=5555, debug=True)