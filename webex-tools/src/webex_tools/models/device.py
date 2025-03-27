"""
Pydantic models for Webex device data.
"""
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class DeviceType(str, Enum):
    """Enum for device types."""
    ROOM = "room"
    DESK = "desk"
    BOARD = "board"
    PHONE = "phone"
    UNKNOWN = "unknown"


class DeviceStatus(str, Enum):
    """Enum for device status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    REGISTERED = "registered"
    UNREGISTERED = "unregistered"
    UNKNOWN = "unknown"


class DeviceCapability(str, Enum):
    """Enum for device capabilities."""
    XAPI = "xapi"
    WEBRTC = "webrtc"
    SIP = "sip"
    SPARK = "spark"
    UNKNOWN = "unknown"


class Device(BaseModel):
    """Model for a Webex device."""
    id: str = Field(..., description="Unique identifier for the device")
    display_name: str = Field(..., description="Display name of the device")
    device_type: DeviceType = Field(DeviceType.UNKNOWN, description="Type of device")
    place_id: Optional[str] = Field(None, description="ID of the place where the device is located")
    tags: List[str] = Field(default_factory=list, description="Tags associated with the device")
    status: DeviceStatus = Field(DeviceStatus.UNKNOWN, description="Current status of the device")
    product: Optional[str] = Field(None, description="Product name")
    capabilities: List[DeviceCapability] = Field(
        default_factory=list, description="Capabilities of the device"
    )
    serial: Optional[str] = Field(None, description="Serial number of the device")
    ip: Optional[str] = Field(None, description="IP address of the device")
    mac: Optional[str] = Field(None, description="MAC address of the device")
    active_since: Optional[str] = Field(None, description="Date and time when the device became active")
    first_seen: Optional[str] = Field(None, description="Date and time when the device was first seen")
    last_seen: Optional[str] = Field(None, description="Date and time when the device was last seen")
    software_version: Optional[str] = Field(None, description="Software version running on the device")
    upgrade_channel: Optional[str] = Field(None, description="Upgrade channel for the device")
    error_code: Optional[str] = Field(None, description="Error code if the device has an error")
    connection_status: Optional[str] = Field(None, description="Connection status of the device")

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "id": "Y2lzY29zcGFyazovL3VzL0RFVklDRS8xMjM0NTY3ODkwYWJjZGVmMTIzNDU2Nzg5MA",
                "display_name": "Conference Room Device",
                "device_type": "room",
                "place_id": "Y2lzY29zcGFyazovL3VzL1BMQUNFL2FiY2RlZjEyMzQ1Njc4OTBhYmNkZWYxMjM0NTY3ODkw",
                "tags": ["floor1", "building2"],
                "status": "active",
                "product": "Cisco Webex Room Kit",
                "capabilities": ["xapi", "webrtc"],
                "serial": "ABC123XYZ",
                "ip": "192.168.1.100",
                "mac": "00:11:22:33:44:55",
                "active_since": "2023-01-15T12:00:00Z",
                "first_seen": "2023-01-15T12:00:00Z",
                "last_seen": "2023-03-27T15:30:00Z",
                "software_version": "ce9.15.0.11",
                "upgrade_channel": "stable",
                "error_code": None,
                "connection_status": "connected"
            }
        }


class DeviceActivationRequest(BaseModel):
    """Model for device activation request."""
    activation_code: str = Field(..., description="Activation code for the device")
    display_name: str = Field(..., description="Display name for the device")
    place_id: Optional[str] = Field(None, description="ID of the place where the device will be located")
    tags: List[str] = Field(default_factory=list, description="Tags to associate with the device")

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "activation_code": "1234-5678-9012-3456",
                "display_name": "Conference Room Device",
                "place_id": "Y2lzY29zcGFyazovL3VzL1BMQUNFL2FiY2RlZjEyMzQ1Njc4OTBhYmNkZWYxMjM0NTY3ODkw",
                "tags": ["floor1", "building2"]
            }
        }


class DeviceCreationRequest(BaseModel):
    """Model for device creation request."""
    display_name: str = Field(..., description="Display name for the device")
    place_id: str = Field(..., description="ID of the place where the device will be located")
    device_type: DeviceType = Field(..., description="Type of device")
    tags: List[str] = Field(default_factory=list, description="Tags to associate with the device")
    product: Optional[str] = Field(None, description="Product name")
    capabilities: List[DeviceCapability] = Field(
        default_factory=list, description="Capabilities of the device"
    )

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "display_name": "Conference Room Device",
                "place_id": "Y2lzY29zcGFyazovL3VzL1BMQUNFL2FiY2RlZjEyMzQ1Njc4OTBhYmNkZWYxMjM0NTY3ODkw",
                "device_type": "room",
                "tags": ["floor1", "building2"],
                "product": "Cisco Webex Room Kit",
                "capabilities": ["xapi", "webrtc"]
            }
        }


class DeviceUpdateRequest(BaseModel):
    """Model for device update request."""
    display_name: Optional[str] = Field(None, description="Display name for the device")
    place_id: Optional[str] = Field(None, description="ID of the place where the device will be located")
    tags: Optional[List[str]] = Field(None, description="Tags to associate with the device")

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "display_name": "Updated Conference Room Device",
                "place_id": "Y2lzY29zcGFyazovL3VzL1BMQUNFL2FiY2RlZjEyMzQ1Njc4OTBhYmNkZWYxMjM0NTY3ODkw",
                "tags": ["floor1", "building2", "updated"]
            }
        }
