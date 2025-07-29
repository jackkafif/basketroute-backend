CANONICAL_ITEMS = {
    "milk": ["whole milk", "skim milk", "2% milk", "almond milk", "oat milk"],
    "mozzarella cheese": ["mozzarella", "shredded mozzarella", "mozzarella cheese block"],
    "bread": ["white bread", "whole wheat bread", "sourdough"],
    "eggs": ["large eggs", "medium eggs", "small eggs"],
    "olive oil": ["olive oil", "extra virgin olive oil"],
    "butter": ["butter", "salted butter", "unsalted butter"],
    "sugar": ["granulated sugar", "brown sugar", "powdered sugar"],
    "salt": ["salt", "table salt", "fine salt"],
    "pepper": ["black pepper", "white pepper", "ground pepper"],
    "cinnamon": ["cinnamon", "ground cinnamon"],
    "vanilla extract": ["vanilla extract", "pure vanilla extract"],
    "chicken": ["chicken", "chicken breasts", "chicken thighs"],
    "beef": ["beef", "beef steaks", "beef roasts"],
    "pasta": ["spaghetti", "fettuccine", "linguine"],
    "tomato": ["tomatoes", "tomato sauce", "tomato paste"],
    "onion": ["onions", "green onions", "red onions"],
    "garlic": ["garlic", "garlic cloves", "garlic powder"],
    "basil": ["basil", "fresh basil", "dried basil"],
    "pepperoni": ["pepperoni", "sliced pepperoni", "ground pepperoni"],
    "mushrooms": ["mushrooms", "shredded mushrooms", "button mushrooms"],
    "bell pepper": ["bell peppers", "green bell peppers", "red bell peppers"],
    "cucumber": ["cucumbers", "cucumber slices", "cucumber juice"],
    "lettuce": ["lettuce", "iceberg lettuce", "romaine lettuce"],
    "avocado": ["avocados", "avocado slices", "avocado halves"],
    "strawberries": ["strawberries", "strawberry jam", "strawberry syrup"],
    "blueberries": ["blueberries", "blueberry jam", "blueberry syrup"],
    "raspberries": ["raspberries", "raspberry jam", "raspberry syrup"],
    "cherries": ["cherries", "cherry jam", "cherry syrup"],
    "pineapple": ["pineapple", "pineapple juice", "pineapple chunks"],
    "mango": ["mango", "mango juice", "mango chunks"],
}

def normalize_item(store_item_name, canonical_map):
    name = store_item_name.lower()
    for general, variants in canonical_map.items():
        for keyword in variants:
            if keyword in name:
                return general
    return None

