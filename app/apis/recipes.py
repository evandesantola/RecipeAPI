''' This script handles the recipes CRUD '''

from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restplus import fields, Namespace, Resource, reqparse

from app import db
from app.models.recipe import Recipe
from ..validation_helper import name_validator
from ..get_helper import manage_get_recipes, manage_get_recipe


api = Namespace(
    'recipes', description='Creating, viewing, editing and deleting recipes')

recipe = api.model('Recipe', {
    'recipe_name': fields.String(required=True, description='Recipe name'),
    'description': fields.String(required=True,
                                 description='Recipe description'),
})

RECIPE_PARSER = reqparse.RequestParser(bundle_errors=True)
RECIPE_PARSER.add_argument(
    'recipe_name', required=True, help='Try again: {error_msg}')
RECIPE_PARSER.add_argument('description', required=True, default='')

EDIT_PARSER = reqparse.RequestParser(bundle_errors=True)
EDIT_PARSER.add_argument(
    'recipe_name', required=False, help='Try again: {error_msg}')
EDIT_PARSER.add_argument('description', required=False, default='')

Q_PARSER = reqparse.RequestParser(bundle_errors=True)
Q_PARSER.add_argument('q', help='search', location='args')
Q_PARSER.add_argument(
    'page', type=int, help='Try again: {error_msg}', location='args')
Q_PARSER.add_argument('per_page', type=int,
                      help='Try again: {error_msg}', location='args')


@api.route('/')
class Recipess(Resource):
    ''' The class handles the view functionality for all recipes '''

    @api.response(200, 'Success')
    @api.expect(Q_PARSER)
    @jwt_required
    def get(self):
        ''' A method to get all the recipes
            Returns all the recipes created by a user or a recipe that matches
            a search keyword

            :return: A recipe that matches the search or a list of recipe\'s
        '''
        user_id = get_jwt_identity()
        the_recipes = Recipe.query.filter_by(created_by=user_id)
        args = Q_PARSER.parse_args(request)
        return manage_get_recipes(the_recipes, args)


@api.route('/<int:category_id>/')
class Recipes(Resource):
    ''' The class handles the Recipes CRUD functionality '''

    @api.response(200, 'Success')
    @api.expect(Q_PARSER)
    @jwt_required
    def get(self, category_id):
        ''' A method to get recipes in a category.
            Checks if a category ID exists and returns all the recipes in the
            category or one with a recipe_name that matches a search keyword

            :param int category_id: The category id to which the recipe belongs
            :return: A recipe that matches the search keyword or all the
            recipes in a category
        '''

        user_id = get_jwt_identity()
        the_recipes = Recipe.query.filter_by(
            created_by=user_id, category_id=category_id)
        args = Q_PARSER.parse_args(request)
        if not the_recipes.all():
            return {'message': f'No recipes in category {category_id}'}, 404
        return manage_get_recipes(the_recipes, args)

    # specifies the expected input fields
    @api.expect(recipe)
    @api.response(201, 'Success')
    @jwt_required
    def post(self, category_id):
        ''' A method to create a recipe.
            Checks if a recipe id exists in the given category, if it doesn\'t
            it creates the new recipe,if it does,it returns a message

            :param int category_id: The category id to which the recipe belongs
            :return: A dictionary with a message and status code
        '''

        user_id = get_jwt_identity()
        args = RECIPE_PARSER.parse_args()
        recipe_name = args.recipe_name
        description = args.description
        category_id = category_id
        created_by = user_id

        validated_name = name_validator(recipe_name)
        if validated_name:
            recipe_name = recipe_name.lower()
            description = description.lower()

            if Recipe.query.filter_by(created_by=created_by,
                                      category_id=category_id,
                                      recipe_name=recipe_name).first() is not None:
                return {'message': 'Recipe already exists'}
            a_recipe = Recipe(recipe_name, description,
                              category_id, created_by)

            db.session.add(a_recipe)
            db.session.commit()
            response = {
                'status': 'Success',
                'message': 'Recipe has been created',
                'recipe_id': a_recipe.recipe_id
            }
            return response, 201
        return {'message': f'{recipe_name} is not a valid name. Recipe names '
                'can only comprise of alphabetical characters and can be more '
                'than one word'}, 400


@api.route('/<int:category_id>/<recipe_id>/')
class Recipee(Resource):
    """This class handles a single recipe GET, PUT AND DELETE functionality
    """

    @api.response(200, 'Category found successfully')
    @jwt_required
    def get(self, category_id, recipe_id):
        ''' A method to get a recipe in a category by id.
            Checks if the given recipe id exists in the given category and
            returns the recipe details.

            :param int category_id: The category id to which the recipe belongs
            :param str recipe_name: The name of the recipe to search for
            :return: The details of the recipe
        '''
        user_id = get_jwt_identity()
        the_recipe = Recipe.query.filter_by(created_by=user_id,
                                            category_id=category_id,
                                            recipe_id=recipe_id).first()
        if the_recipe is not None:
            return manage_get_recipe(the_recipe)
        return {'message': f'You don\'t have a recipe with id {recipe_id}'}, 404

    @api.expect(EDIT_PARSER)
    @api.response(204, 'Success')
    @jwt_required
    def put(self, category_id, recipe_id):
        ''' A method for editing a recipe.
            Checks if the given recipe id exists in the given category and
            edits it with the new details.

            :param str recipe_id: The new recipe id
            :param str description: The new recipe description
            :return: A dictionary with a message
        '''
        user_id = get_jwt_identity()
        the_recipe = Recipe.query.filter_by(created_by=user_id,
                                            category_id=category_id,
                                            recipe_id=recipe_id).first()

        if the_recipe is None:
            return {'message': f'No recipe with id {recipe_id}'}, 404
        args = EDIT_PARSER.parse_args()
        recipe_name = args.recipe_name
        description = args.description

        if not recipe_name:
            recipe_name = the_recipe.recipe_name
        if not description:
            description = the_recipe.ingredients

        recipe_name = recipe_name.lower()
        description = description.lower()

        validated_name = name_validator(recipe_name)
        if validated_name:
            the_recipe.recipe_name = recipe_name
            the_recipe.ingredients = description
            db.session.add(the_recipe)
            db.session.commit()
            response = {
                'status': 'Success',
                'message': 'Recipe details successfully edited'
            }
            return response, 200
        return {'message': 'The recipe name should comprise alphabetical'
                ' characters and can be more than one word'}

    @api.response(204, 'Success')
    @jwt_required
    def delete(self, category_id, recipe_id):
        ''' A method to delete a recipe
            Checks if the given recipe id exists in the given category and
            deletes it.

            :param str recipe_id: The new recipe id
            :param str description: The new recipe description
            :return: A dictionary with a message
        '''
        user_id = get_jwt_identity()
        the_recipe = Recipe.query.filter_by(created_by=user_id,
                                            category_id=category_id,
                                            recipe_id=recipe_id).first()
        if the_recipe is None:
            return {'message': f'recipe id {recipe_id} does not exist'}
        db.session.delete(the_recipe)
        db.session.commit()
        return {'message': 'Recipe was deleted'}
