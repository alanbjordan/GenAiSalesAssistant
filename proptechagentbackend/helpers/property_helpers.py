from database import db
from models.sql_models import Property, Building

def fetch_properties(filter_params: dict) -> list:
    """
    Query the Property table (and optionally Building) based on certain filters.
    
    :param filter_params: A dictionary with keys such as:
        {
          "bedrooms": <int>,         # Minimum number of bedrooms
          "max_bedrooms": <int>,       # Maximum number of bedrooms
          "bathrooms": <int>,          # Minimum number of bathrooms
          "max_bathrooms": <int>,      # Maximum number of bathrooms
          "price": <float>,            # Minimum rental price
          "max_price": <float>,        # Maximum rental price
          "sq_meters": <float>,        # Minimum size in square meters
          "max_sq_meters": <float>,    # Maximum size in square meters
          "distance_from_bts": <float>,# Maximum distance from the nearest BTS station in kilometers
          "property_name": <str>,      # Property name search (matches building name)
          "building_name": <str>,      # Building name search,
          "property_code": <str>       # Unique property code for narrowing the results
        }
    :return: A list of dictionaries, each representing a property.
    """
    query = db.session.query(Property).join(Building, Property.building_id == Building.id)

    # Bedrooms range filter
    if "bedrooms" in filter_params:
        query = query.filter(Property.bedrooms >= filter_params["bedrooms"])
    if "max_bedrooms" in filter_params:
        query = query.filter(Property.bedrooms <= filter_params["max_bedrooms"])

    # Bathrooms range filter
    if "bathrooms" in filter_params:
        query = query.filter(Property.bathrooms >= filter_params["bathrooms"])
    if "max_bathrooms" in filter_params:
        query = query.filter(Property.bathrooms <= filter_params["max_bathrooms"])

    # Price range filter
    if "price" in filter_params:
        query = query.filter(Property.price >= filter_params["price"])
    if "max_price" in filter_params:
        query = query.filter(Property.price <= filter_params["max_price"])

    # Size (sq_meters) range filter
    if "sq_meters" in filter_params:
        query = query.filter(Property.size >= filter_params["sq_meters"])
    if "max_sq_meters" in filter_params:
        query = query.filter(Property.size <= filter_params["max_sq_meters"])

    # Distance from BTS filter (assumes a maximum acceptable distance)
    if "distance_from_bts" in filter_params:
        query = query.filter(Building.distance_to_bts <= filter_params["distance_from_bts"])

    # Filter by property_name (using building name as a proxy)
    if "property_name" in filter_params:
        query = query.filter(Building.name.ilike(f"%{filter_params['property_name']}%"))

    # Filter by building_name directly
    if "building_name" in filter_params:
        query = query.filter(Building.name.ilike(f"%{filter_params['building_name']}%"))

    # Filter by property_code if provided
    if "property_code" in filter_params:
        query = query.filter(Property.property_code == filter_params["property_code"])

    results = query.all()

    def to_dict(prop: Property) -> dict:
        no_image_url = "https://pub-5639854ae5864779be6f398a0fa1c555.r2.dev/noimageyet.jpg"
        images = []
        if prop.photo_urls:
            # Ensure photo_urls is a dict (jsonb column should already be a dict)
            photo_dict = prop.photo_urls if isinstance(prop.photo_urls, dict) else {}
            # Loop through every key in the photo_urls dict
            for key, url_list in photo_dict.items():
                if isinstance(url_list, list):
                    images.extend([url for url in url_list if url != no_image_url])
        return {
            "property_code": prop.property_code,
            "building_name": prop.building_name or (prop.building.name if prop.building else None),
            "bedrooms": prop.bedrooms,
            "bathrooms": prop.bathrooms,
            "price": float(prop.price) if prop.price is not None else None,
            "size_sqm": float(prop.size) if prop.size is not None else None,
            "created_at": prop.created_at.isoformat() if prop.created_at else None,
            "images": images
        }

    return [to_dict(p) for p in results]
