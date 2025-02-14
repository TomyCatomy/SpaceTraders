from pydantic import BaseModel

from models.fleet.ship_nav import ShipNav


class OrbitShipResponse(BaseModel):
    nav: ShipNav