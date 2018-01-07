# app/apis/helper.py
''' This script handles search and pagination functionality for recipes '''

# THird party imports
import jsonify

# Local imports
from ..serializers import RecipeSchema
from .categories import per_page_max, per_page_min


def manage_get(the_recipes, args):
    """ Function to handle search and pagination
        It receives a BaseQuery object of recipes, checks if the search
        parameter was passed a value and searches for that value.
        If the pagination parameters were passed values, checks if they are
        within the min/max range per page and paginates accordingly.

        :param object the_recipes: -- [description]
        :param list args: -- [description]
        :return:
    """

    if the_recipes:
        q = args.get('q', '')
        page = args.get('page', 1)
        per_page = args.get('per_page', 10)
        if per_page is None or per_page < per_page_min:
            per_page = per_page_min
        if per_page > per_page_max:
            per_page = per_page_max
        if q:
            q = q.lower()
            for a_recipe in the_recipes.all():
                if q in a_recipe.recipe_name.lower():
                    recipeschema = RecipeSchema()
                    the_recipe = recipeschema.dump(a_recipe)
                    return jsonify(the_recipe.data)
        pag_recipes = the_recipes.paginate(
            page, per_page, error_out=False)
        paginated = []
        for a_recipe in pag_recipes.items:
            paginated.append(a_recipe)
        recipesschema = RecipeSchema(many=True)
        all_recipes = recipesschema.dump(paginated)
        return jsonify(all_recipes)
    return {'message': 'There are no recipes'}