"""Tests for CategoryService."""

from core.schemas import CategoryCreate, CategoryUpdate


class TestCategoryService:
    def test_create_category(self, category_service):
        data = CategoryCreate(
            name="Transport",
            icon="directions_car",
            color="#00FF00",
        )
        cat = category_service.create(data)
        assert cat.id is not None
        assert cat.name == "Transport"
        assert cat.monthly_budget is None

    def test_seed_defaults(self, category_service):
        category_service.seed_defaults()
        categories = category_service.list_all()
        assert len(categories) == 7

        category_service.seed_defaults()
        assert len(category_service.list_all()) == 7

    def test_update_category(self, category_service):
        data = CategoryCreate(name="Food", icon="restaurant", color="#FF0000")
        cat = category_service.create(data)
        updated = category_service.update(
            cat.id,
            CategoryUpdate(name="Comida", color="#00FF00"),
        )
        assert updated is not None
        assert updated.name == "Comida"
        assert updated.color == "#00FF00"
