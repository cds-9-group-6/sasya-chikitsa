"""
Vendor Tool for LangGraph Workflow

This tool provides vendor information and pricing for treatment products.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
import random
import json
import sys
import os

logger = logging.getLogger(__name__)


class VendorInput(BaseModel):
    """Input schema for vendor tool"""
    treatments: List[Dict[str, Any]] = Field(description="List of recommended treatments")
    location: Optional[str] = Field(default="", description="User location for local vendors")
    user_preferences: Optional[Dict[str, Any]] = Field(default={}, description="User preferences (organic, budget, etc.)")


class VendorTool(BaseTool):
    """
    Tool for finding vendor information and pricing
    """
    name: str = "vendor_finder"
    description: str = "Finds local vendors and pricing information for plant treatment products"
    args_schema: type[BaseModel] = VendorInput
    
    # Declare the vendor_database field properly
    vendor_database: Dict[str, Any] = Field(default_factory=dict, exclude=True)
    
    def __init__(self, **data):
        super().__init__(**data)
        self.vendor_database = self._load_vendor_database()
    
    def _load_vendor_database(self) -> Dict[str, Any]:
        """Load vendor database (simulated data)"""
        # In production, this would connect to actual vendor APIs or databases
        return {
            "vendors": [
                {
                    "id": "v001",
                    "name": "AgroSupply India",
                    "type": "Agricultural Store",
                    "locations": ["Tamil Nadu", "Karnataka", "Andhra Pradesh"],
                    "contact": "+91-9876543210",
                    "website": "www.agrosupplyindia.com",
                    "delivery_options": "Home delivery available",
                    "specializes": ["Chemical pesticides", "Fertilizers"],
                    "rating": 4.2,
                    "organic_available": False
                },
                {
                    "id": "v002", 
                    "name": "Green Earth Organics",
                    "type": "Organic Supplier",
                    "locations": ["Tamil Nadu", "Kerala"],
                    "contact": "+91-8765432109",
                    "website": "www.greenearthorganics.in",
                    "delivery_options": "Express delivery in 2-3 days",
                    "specializes": ["Organic treatments", "Neem products", "Bio-fertilizers"],
                    "rating": 4.6,
                    "organic_available": True
                },
                {
                    "id": "v003",
                    "name": "FarmTech Solutions",
                    "type": "Agricultural Technology",
                    "locations": ["All India"],
                    "contact": "+91-7654321098", 
                    "website": "www.farmtechsolutions.com",
                    "delivery_options": "Nationwide delivery",
                    "specializes": ["Modern pesticides", "Smart farming tools"],
                    "rating": 4.1,
                    "organic_available": False
                },
                {
                    "id": "v004",
                    "name": "Nature's Care",
                    "type": "Eco-friendly Store",
                    "locations": ["Tamil Nadu", "Karnataka"],
                    "contact": "+91-6543210987",
                    "website": "www.naturescare.co.in",
                    "delivery_options": "Local delivery within 24 hours",
                    "specializes": ["Organic solutions", "Natural pesticides", "Compost"],
                    "rating": 4.4,
                    "organic_available": True
                },
                {
                    "id": "v005",
                    "name": "Agricultural Mart",
                    "type": "General Store", 
                    "locations": ["Tamil Nadu", "Andhra Pradesh", "Kerala"],
                    "contact": "+91-5432109876",
                    "website": "www.agriculturalmart.in",
                    "delivery_options": "Home delivery and pickup available",
                    "specializes": ["General agricultural supplies", "Seeds", "Tools"],
                    "rating": 3.9,
                    "organic_available": True
                }
            ],
            "products": {
                "copper sulfate fungicide": {
                    "category": "fungicide",
                    "organic": False,
                    "brands": ["Tata Rallis", "UPL", "Dhanuka"],
                    "sizes": ["100ml", "250ml", "500ml", "1L"],
                    "price_ranges": {
                        "100ml": [80, 120],
                        "250ml": [180, 220],
                        "500ml": [320, 380],
                        "1L": [580, 650]
                    }
                },
                "neem oil solution": {
                    "category": "organic_pesticide",
                    "organic": True,
                    "brands": ["Neemazal", "Fortune Biotech", "Godrej"],
                    "sizes": ["100ml", "250ml", "500ml", "1L"],
                    "price_ranges": {
                        "100ml": [90, 140],
                        "250ml": [200, 260],
                        "500ml": [380, 450],
                        "1L": [700, 820]
                    }
                },
                "copper-based bactericide": {
                    "category": "bactericide",
                    "organic": False,
                    "brands": ["BASF", "Bayer", "Syngenta"],
                    "sizes": ["100ml", "250ml", "500ml"],
                    "price_ranges": {
                        "100ml": [120, 160],
                        "250ml": [280, 340],
                        "500ml": [520, 620]
                    }
                },
                "streptomycin solution": {
                    "category": "antibiotic",
                    "organic": False,
                    "brands": ["Pfizer", "Zuventus", "Dhanuka"],
                    "sizes": ["10g", "25g", "50g"],
                    "price_ranges": {
                        "10g": [150, 200],
                        "25g": [350, 450],
                        "50g": [650, 800]
                    }
                },
                "imidacloprid insecticide": {
                    "category": "insecticide", 
                    "organic": False,
                    "brands": ["Confidor", "Admire", "Tatamida"],
                    "sizes": ["100ml", "250ml", "500ml"],
                    "price_ranges": {
                        "100ml": [200, 280],
                        "250ml": [450, 550],
                        "500ml": [850, 1000]
                    }
                },
                "organic compost tea": {
                    "category": "organic_fertilizer",
                    "organic": True,
                    "brands": ["Terra Vita", "Bio Grow", "Nature's Best"],
                    "sizes": ["500ml", "1L", "2L"],
                    "price_ranges": {
                        "500ml": [120, 180],
                        "1L": [220, 300],
                        "2L": [400, 520]
                    }
                },
                "broad spectrum fungicide": {
                    "category": "fungicide",
                    "organic": False,
                    "brands": ["Antracol", "Mancozeb", "Indofil"],
                    "sizes": ["100g", "250g", "500g", "1kg"],
                    "price_ranges": {
                        "100g": [80, 120],
                        "250g": [180, 240],
                        "500g": [320, 420],
                        "1kg": [580, 720]
                    }
                }
            }
        }
    
    async def _arun(self, **kwargs) -> Dict[str, Any]:
        """Async implementation"""
        return await asyncio.to_thread(self._run, **kwargs)
    
    def _run(self, **kwargs) -> Dict[str, Any]:
        """
        Run the vendor tool
        
        Returns:
            Dictionary containing vendor information or error
        """
        try:
            treatments = kwargs.get("treatments", [])
            location = kwargs.get("location", "").lower()
            user_preferences = kwargs.get("user_preferences", {})
            
            if not treatments:
                return {"error": "No treatments provided"}
            
            # Filter vendors based on location
            available_vendors = self._filter_vendors_by_location(location)
            
            # Filter by user preferences (organic, etc.)
            if user_preferences.get("organic_only"):
                available_vendors = [v for v in available_vendors if v.get("organic_available")]
            
            # Generate vendor options with pricing
            vendor_options = []
            
            for vendor in available_vendors[:3]:  # Limit to top 3 vendors
                vendor_option = self._generate_vendor_option(vendor, treatments, user_preferences)
                if vendor_option:
                    vendor_options.append(vendor_option)
            
            if not vendor_options:
                return {
                    "vendors": [],
                    "message": "No vendors found in your area. Please check with local agricultural stores."
                }
            
            # Sort by total price or rating
            sort_by = user_preferences.get("sort_by", "price")
            if sort_by == "rating":
                vendor_options.sort(key=lambda x: x.get("rating", 0), reverse=True)
            else:
                vendor_options.sort(key=lambda x: x.get("total_price", 999999))
            
            logger.info(f"Found {len(vendor_options)} vendor options")
            
            return {
                "vendors": vendor_options,
                "location": location,
                "total_vendors_checked": len(available_vendors)
            }
            
        except Exception as e:
            error_msg = f"Vendor search error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"error": error_msg}
    
    def _filter_vendors_by_location(self, location: str) -> List[Dict[str, Any]]:
        """Filter vendors by location"""
        if not location:
            return self.vendor_database["vendors"]
        
        filtered_vendors = []
        for vendor in self.vendor_database["vendors"]:
            vendor_locations = [loc.lower() for loc in vendor.get("locations", [])]
            
            # Check if location matches or if vendor serves "All India"
            if (any(location in loc or loc in location for loc in vendor_locations) or 
                "all india" in vendor_locations):
                filtered_vendors.append(vendor)
        
        return filtered_vendors if filtered_vendors else self.vendor_database["vendors"]
    
    def _generate_vendor_option(self, vendor: Dict[str, Any], treatments: List[Dict[str, Any]], user_preferences: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate vendor option with pricing for treatments"""
        try:
            vendor_items = []
            total_price = 0
            
            for treatment in treatments:
                treatment_name = treatment.get("name", "").lower()
                treatment_type = treatment.get("type", "").lower()
                
                # Match treatment to products
                product_match = self._find_matching_product(treatment_name, treatment_type)
                
                if product_match:
                    product_data = self.vendor_database["products"][product_match]
                    
                    # Skip organic products for non-organic vendors and vice versa
                    if user_preferences.get("organic_only") and not product_data.get("organic"):
                        continue
                    if not vendor.get("organic_available") and product_data.get("organic"):
                        continue
                    
                    # Select appropriate size and calculate price
                    size = self._select_product_size(product_data, user_preferences)
                    price_range = product_data["price_ranges"][size]
                    price = random.randint(price_range[0], price_range[1])
                    
                    # Select brand
                    brand = random.choice(product_data["brands"])
                    
                    vendor_items.append({
                        "name": treatment.get("name"),
                        "product_name": product_match.title(),
                        "brand": brand,
                        "size": size,
                        "price": price,
                        "category": product_data["category"],
                        "organic": product_data.get("organic", False)
                    })
                    
                    total_price += price
            
            if not vendor_items:
                return None
            
            # Add delivery charges
            delivery_charge = self._calculate_delivery_charge(vendor, total_price)
            total_price += delivery_charge
            
            return {
                "vendor_id": vendor["id"],
                "name": vendor["name"],
                "type": vendor["type"],
                "location": vendor["locations"][0] if vendor["locations"] else "Unknown",
                "contact": vendor["contact"],
                "website": vendor.get("website"),
                "delivery_options": vendor["delivery_options"],
                "rating": vendor["rating"],
                "items": vendor_items,
                "subtotal": total_price - delivery_charge,
                "delivery_charge": delivery_charge,
                "total_price": total_price,
                "estimated_delivery": self._get_delivery_estimate(vendor),
                "specializes": vendor.get("specializes", [])
            }
            
        except Exception as e:
            logger.error(f"Error generating vendor option: {str(e)}")
            return None
    
    def _find_matching_product(self, treatment_name: str, treatment_type: str) -> Optional[str]:
        """Find matching product in database"""
        products = self.vendor_database["products"]
        
        # Direct name matching
        for product_key in products.keys():
            if any(word in product_key for word in treatment_name.split() if len(word) > 3):
                return product_key
        
        # Category-based matching
        category_mapping = {
            "chemical": ["fungicide", "bactericide", "insecticide"],
            "organic": ["organic_pesticide", "organic_fertilizer"],
            "fungicide": ["fungicide"],
            "bactericide": ["bactericide"],
            "antibiotic": ["antibiotic"],
            "insecticide": ["insecticide"]
        }
        
        treatment_category = category_mapping.get(treatment_type.lower(), [])
        
        for product_key, product_data in products.items():
            if product_data["category"] in treatment_category:
                return product_key
        
        # Fallback to broad spectrum
        return "broad spectrum fungicide"
    
    def _select_product_size(self, product_data: Dict[str, Any], user_preferences: Dict[str, Any]) -> str:
        """Select appropriate product size based on preferences"""
        available_sizes = list(product_data["price_ranges"].keys())
        
        # User preference for size
        preferred_size = user_preferences.get("preferred_size", "medium")
        
        if preferred_size == "small":
            return available_sizes[0]
        elif preferred_size == "large" and len(available_sizes) > 2:
            return available_sizes[-1]
        else:
            # Medium or default - select middle size
            return available_sizes[len(available_sizes) // 2] if len(available_sizes) > 1 else available_sizes[0]
    
    def _calculate_delivery_charge(self, vendor: Dict[str, Any], subtotal: int) -> int:
        """Calculate delivery charges"""
        if subtotal > 1000:
            return 0  # Free delivery for orders above ₹1000
        elif vendor.get("type") == "Agricultural Technology":
            return 100  # Higher delivery for specialized vendors
        else:
            return 50  # Standard delivery charge
    
    def _get_delivery_estimate(self, vendor: Dict[str, Any]) -> str:
        """Get delivery time estimate"""
        vendor_type = vendor.get("type", "")
        delivery_options = vendor.get("delivery_options", "")
        
        if "express" in delivery_options.lower():
            return "2-3 business days"
        elif "24 hours" in delivery_options.lower():
            return "Within 24 hours"
        elif "nationwide" in delivery_options.lower():
            return "5-7 business days"
        else:
            return "3-5 business days"


# Async wrapper for compatibility
async def run_vendor_tool(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Async wrapper for the vendor tool
    
    Args:
        input_data: Dictionary containing treatments and location info
    
    Returns:
        Vendor information or error
    """
    tool = VendorTool()
    return await tool._arun(**input_data)
