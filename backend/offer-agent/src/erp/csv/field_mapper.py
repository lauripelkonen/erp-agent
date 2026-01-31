"""
CSV Field Mapper

Maps between generic domain models and CSV file formats.
This centralized mapping layer makes it easy to understand and maintain
all CSV-specific field transformations.
"""
from typing import Dict, Any
from src.domain.product import Product


class CSVFieldMapper:
    """
    Maps between generic domain models and CSV file formats.

    This class centralizes all knowledge about CSV field names,
    making it easier to:
    - Understand CSV-specific requirements
    - Maintain field mappings in one place
    - Add new fields without changing business logic
    """

    # CSV column name mappings (Finnish to English)
    CSV_COLUMNS = {
        'Tuotekoodi': 'product_code',
        'Laatu': 'quality',
        'Määrittely': 'specification',
        'Tuotenimi': 'product_name',
        'Paksuus': 'thickness',
        'Tuoteryhmä': 'product_group',
        'Lisänimi': 'extra_name',
        'Halkaisija': 'diameter',
        'Seinämä': 'wall',
        'Muu mitta': 'other_dimension',
        'Pinta': 'surface',
        'Yksikkö paino': 'unit_weight',
        'Paineluokka': 'pressure_class',
        'Lisätiedot': 'additional_info',
        'Toleranssi': 'tolerance',
        'Sisähalkaisija': 'inner_diameter',
        'Leveys': 'width',
        'Korkeus/pituus': 'height_length',
        'Eräkoko': 'batch_size'
    }

    def to_product(self, csv_data: Dict[str, Any]) -> Product:
        """
        Convert CSV product data to generic Product model.

        Args:
            csv_data: Raw product data from CSV file

        Returns:
            Generic Product domain model
        """
        # Build product name from available fields
        product_name = csv_data.get('Tuotenimi', '').strip()

        # Build description from specification and extra details
        description_parts = []
        if csv_data.get('Määrittely'):
            description_parts.append(str(csv_data['Määrittely']).strip())
        if csv_data.get('Lisänimi'):
            description_parts.append(str(csv_data['Lisänimi']).strip())
        if csv_data.get('Laatu'):
            description_parts.append(f"Laatu: {csv_data['Laatu']}")

        description = ' | '.join(description_parts) if description_parts else None

        # Extract product group
        product_group = str(csv_data.get('Tuoteryhmä', '')).strip()

        # Extract unit weight as price (since CSV doesn't have price column)
        # Default to unit weight or 0.0
        unit_weight = csv_data.get('Yksikkö paino', 0)
        try:
            unit_price = float(unit_weight) if unit_weight else 0.0
        except (ValueError, TypeError):
            unit_price = 0.0

        # Extract extra name (Lisänimi)
        extra_name = str(csv_data.get('Lisänimi', '')).strip() or None

        return Product(
            code=str(csv_data.get('Tuotekoodi', '')).strip(),
            name=product_name,
            description=description,
            extra_name=extra_name,
            unit='KPL',  # Default unit
            product_group=product_group if product_group else None,
            list_price=unit_price,
            unit_price=unit_price,
            price=unit_price,
            stock_quantity=None,  # CSV doesn't have stock info
            stock_location=None,
            active=True,
            erp_metadata=csv_data
        )

    def to_search_result(self, csv_data: Dict[str, Any], priority: str = 'non_priority') -> Dict[str, Any]:
        """
        Convert CSV product data to search result format expected by ProductMatcher.

        Args:
            csv_data: Raw product data from CSV file
            priority: Priority level ('priority' or 'non_priority')

        Returns:
            Dict in format expected by ProductMatcher
        """
        product_code = str(csv_data.get('Tuotekoodi', '')).strip()
        product_name = csv_data.get('Tuotenimi', '').strip()
        extra_name = csv_data.get('Lisänimi', '').strip()
        specification = csv_data.get('Määrittely', '').strip()

        # Build description
        description_parts = []
        if specification:
            description_parts.append(specification)
        if csv_data.get('Laatu'):
            description_parts.append(f"Laatu: {csv_data['Laatu']}")
        if csv_data.get('Lisätiedot'):
            description_parts.append(str(csv_data['Lisätiedot']))

        description = ' | '.join(description_parts) if description_parts else ''

        # Extract unit weight as price
        unit_weight = csv_data.get('Yksikkö paino', 0)
        try:
            price = float(unit_weight) if unit_weight else 0.0
        except (ValueError, TypeError):
            price = 0.0

        # Product group code
        product_group = csv_data.get('Tuoteryhmä', '')
        try:
            group_code = int(product_group) if product_group else 0
        except (ValueError, TypeError):
            group_code = 0

        return {
            'id': product_code,
            'sku': product_code,
            'name': product_name,
            'extra_name': extra_name,
            'price': price,
            'product_searchcode': specification,  # Use specification as search code
            'description': description,
            'group_code': group_code,
            'priority': priority,
            'total_stock': 0.0,  # CSV doesn't have stock info
            'yearly_sales_qty': 0.0,  # CSV doesn't have sales info
            'data_source': 'CSV_FILE'
        }

    def classify_product_priority(self, group_code: int) -> str:
        """
        Classify product as priority or non-priority based on group code.

        Similar to Lemonsoft logic: group codes 1-999 are priority products.

        Args:
            group_code: Product group code

        Returns:
            'priority' or 'non_priority'
        """
        return 'priority' if group_code < 1000 else 'non_priority'
