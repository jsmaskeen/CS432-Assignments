import unittest
import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from database.db_manager import DatabaseManager

class TestForeignKeys(unittest.TestCase):
    def setUp(self):
        self.db_manager = DatabaseManager()
        self.db = self.db_manager.create_database("test_db")

        self.db.create_table(
            name="users",
            columns=["user_id", "name"],
            primary_key="user_id"
        )

        self.db.create_table(
            name="posts",
            columns=["post_id", "content", "author_id"],
            primary_key="post_id",
            foreign_keys=[
                {
                    "column": "author_id",
                    "references_table": "users",
                    "references_column": "user_id"
                }
            ]
        )

        users_table = self.db.get_table("users")
        users_table.insert_row({"user_id": 1, "name": "Alice"})
        users_table.insert_row({"user_id": 2, "name": "Bob"})

    def test_insert_success(self):
        posts_table = self.db.get_table("posts")
        posts_table.insert_row({"post_id": 101, "content": "Hello from Alice", "author_id": 1})
        self.assertIsNotNone(posts_table.select(101))

    def test_insert_failure_nonexistent_foreign_key(self):
        posts_table = self.db.get_table("posts")
        with self.assertRaises(ValueError):
            posts_table.insert_row({"post_id": 102, "content": "Invalid post", "author_id": 99})

    def test_update_success(self):
        posts_table = self.db.get_table("posts")
        posts_table.insert_row({"post_id": 103, "content": "Initial post", "author_id": 1})
        posts_table.update_row(103, {"author_id": 2})
        updated_post = posts_table.select(103)
        self.assertEqual(updated_post["author_id"], 2)

    def test_update_failure_nonexistent_foreign_key(self):
        posts_table = self.db.get_table("posts")
        posts_table.insert_row({"post_id": 104, "content": "Another post", "author_id": 1})
        with self.assertRaises(ValueError):
            posts_table.update_row(104, {"author_id": 99})

    def test_delete_failure_referenced_row(self):
        posts_table = self.db.get_table("posts")
        posts_table.insert_row({"post_id": 105, "content": "A post by Alice", "author_id": 1})
        
        users_table = self.db.get_table("users")
        with self.assertRaises(ValueError):
            users_table.delete_row(1)

    def test_delete_success_unreferenced_row(self):
        users_table = self.db.get_table("users")
        users_table.delete_row(2)
        self.assertIsNone(users_table.select(2))

    def test_insert_null_foreign_key(self):
        posts_table = self.db.get_table("posts")
        # Should succeed if foreign key is None, imitating a nullable field
        posts_table.insert_row({"post_id": 106, "content": "Anonymous post", "author_id": None})
        self.assertIsNotNone(posts_table.select(106))

    def test_multiple_foreign_keys(self):
        self.db.create_table(
            name="categories",
            columns=["category_id", "category_name"],
            primary_key="category_id"
        )
        self.db.get_table("categories").insert_row({"category_id": 1, "category_name": "Tech"})
        
        self.db.create_table(
            name="post_categories",
            columns=["pc_id", "post_id", "category_id"],
            primary_key="pc_id",
            foreign_keys=[
                {"column": "post_id", "references_table": "posts", "references_column": "post_id"},
                {"column": "category_id", "references_table": "categories", "references_column": "category_id"}
            ]
        )
        
        posts_table = self.db.get_table("posts")
        posts_table.insert_row({"post_id": 107, "content": "Tech post", "author_id": 1})
        
        pc_table = self.db.get_table("post_categories")
        pc_table.insert_row({"pc_id": 1, "post_id": 107, "category_id": 1})
        self.assertIsNotNone(pc_table.select(1))
        
        # Test violation on first FK
        with self.assertRaises(ValueError):
            pc_table.insert_row({"pc_id": 2, "post_id": 999, "category_id": 1})
            
        # Test violation on second FK
        with self.assertRaises(ValueError):
            pc_table.insert_row({"pc_id": 3, "post_id": 107, "category_id": 999})
            
        # Test deletion violation on categories
        with self.assertRaises(ValueError):
            self.db.get_table("categories").delete_row(1)

        # Remove mapping, then delete should work
        pc_table.delete_row(1)
        self.db.get_table("categories").delete_row(1)
        self.assertIsNone(self.db.get_table("categories").select(1))

    def test_delete_cascade_recursive(self):
        # Region -> Country -> State -> City
        self.db.create_table(
            name="regions", columns=["region_id", "name"], primary_key="region_id"
        )
        self.db.create_table(
            name="countries", columns=["country_id", "region_id", "name"], primary_key="country_id",
            foreign_keys=[{"column": "region_id", "references_table": "regions", "references_column": "region_id", "on_delete": "CASCADE"}]
        )
        self.db.create_table(
            name="states", columns=["state_id", "country_id", "name"], primary_key="state_id",
            foreign_keys=[{"column": "country_id", "references_table": "countries", "references_column": "country_id", "on_delete": "CASCADE"}]
        )
        self.db.create_table(
            name="cities", columns=["city_id", "state_id", "name"], primary_key="city_id",
            foreign_keys=[{"column": "state_id", "references_table": "states", "references_column": "state_id", "on_delete": "CASCADE"}]
        )

        regions = self.db.get_table("regions")
        countries = self.db.get_table("countries")
        states = self.db.get_table("states")
        cities = self.db.get_table("cities")

    
        regions.insert_row({"region_id": 1, "name": "North America"})
        countries.insert_row({"country_id": 1, "region_id": 1, "name": "USA"})
        states.insert_row({"state_id": 1, "country_id": 1, "name": "California"})
        cities.insert_row({"city_id": 1, "state_id": 1, "name": "Los Angeles"})
        cities.insert_row({"city_id": 2, "state_id": 1, "name": "San Francisco"})

        self.assertIsNotNone(cities.select(1))
        self.assertIsNotNone(cities.select(2))

        # cascade delete on the top level (Region)
        regions.delete_row(1)

        self.assertIsNone(regions.select(1))
        self.assertIsNone(countries.select(1))
        self.assertIsNone(states.select(1))
        self.assertIsNone(cities.select(1))
        self.assertIsNone(cities.select(2))

    def tearDown(self):
        self.db_manager.delete_database("test_db")

if __name__ == "__main__":
    unittest.main()
