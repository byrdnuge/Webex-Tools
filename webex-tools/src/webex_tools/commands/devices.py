"""
Commands for managing Webex devices.
"""
import csv
import json
import os
import sys
from typing import List, Optional

import rich_click as click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from webex_tools.models.device import DeviceActivationRequest, DeviceCreationRequest, DeviceType
from webex_tools.utils.api import WebexAPI
from webex_tools.utils.formatting import (
    create_table,
    format_dict_as_table,
    format_error,
    format_success,
    format_warning,
)

console = Console()

@click.group(name="devices", help="Commands for managing Webex devices.")
def devices_group():
    """Group for device-related commands."""
    pass


@devices_group.command(name="activate", help="Activate a Webex device.")
@click.argument("activation_code", required=True)
@click.argument("display_name", required=True)
@click.option(
    "--place-id",
    help="ID of the place where the device will be located.",
)
@click.option(
    "--tags",
    help="Comma-separated list of tags to associate with the device.",
)
@click.pass_context
def activate_device(
    ctx: click.Context,
    activation_code: str,
    display_name: str,
    place_id: Optional[str] = None,
    tags: Optional[str] = None,
) -> None:
    """
    Activate a Webex device using its activation code.
    
    Args:
        ctx: Click context.
        activation_code: Activation code for the device.
        display_name: Display name for the device.
        place_id: ID of the place where the device will be located.
        tags: Comma-separated list of tags to associate with the device.
    """
    debug = ctx.obj.get("DEBUG", False)
    
    # Parse tags
    tag_list = []
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
    
    # Create activation request model
    try:
        activation_request = DeviceActivationRequest(
            activation_code=activation_code,
            display_name=display_name,
            place_id=place_id,
            tags=tag_list,
        )
    except Exception as e:
        console.print(format_error(f"Invalid input: {str(e)}"))
        sys.exit(1)
    
    # Activate device
    try:
        api = WebexAPI()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Activating device...[/bold blue]"),
            console=console,
        ) as progress:
            progress.add_task("activate", total=None)
            
            # Make API call to activate device
            response = api.post(
                "devices/activations",
                {
                    "activationCode": activation_request.activation_code,
                    "displayName": activation_request.display_name,
                    "placeId": activation_request.place_id,
                    "tags": activation_request.tags,
                },
            )
        
        # Display success message
        console.print(format_success(f"Device '{display_name}' activated successfully!"))
        
        # Display device details if in debug mode
        if debug and response:
            console.print(format_dict_as_table(response, title="Device Details"))
    
    except Exception as e:
        console.print(format_error(f"Failed to activate device: {str(e)}"))
        sys.exit(1)


@devices_group.command(name="activate-batch", help="Activate multiple Webex devices from a CSV file.")
@click.argument("csv_file", type=click.Path(exists=True), required=True)
@click.pass_context
def activate_devices_batch(ctx: click.Context, csv_file: str) -> None:
    """
    Activate multiple Webex devices from a CSV file.
    
    The CSV file should have the following columns:
    - activation_code: Activation code for the device.
    - display_name: Display name for the device.
    - place_id: (Optional) ID of the place where the device will be located.
    - tags: (Optional) Comma-separated list of tags to associate with the device.
    
    Args:
        ctx: Click context.
        csv_file: Path to CSV file with device information.
    """
    debug = ctx.obj.get("DEBUG", False)
    
    try:
        # Read CSV file
        devices = []
        with open(csv_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Parse tags
                tag_list = []
                if "tags" in row and row["tags"]:
                    tag_list = [tag.strip() for tag in row["tags"].split(",")]
                
                # Create activation request model
                try:
                    activation_request = DeviceActivationRequest(
                        activation_code=row["activation_code"],
                        display_name=row["display_name"],
                        place_id=row.get("place_id"),
                        tags=tag_list,
                    )
                    devices.append(activation_request)
                except Exception as e:
                    console.print(format_warning(f"Skipping invalid device '{row.get('display_name', 'Unknown')}': {str(e)}"))
        
        if not devices:
            console.print(format_error("No valid devices found in CSV file."))
            sys.exit(1)
        
        # Activate devices
        api = WebexAPI()
        
        success_count = 0
        error_count = 0
        errors = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Activating devices...[/bold blue] {task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("", total=len(devices), description=f"0/{len(devices)}")
            
            for i, device in enumerate(devices):
                progress.update(task, description=f"{i}/{len(devices)}")
                
                try:
                    # Make API call to activate device
                    api.post(
                        "devices/activations",
                        {
                            "activationCode": device.activation_code,
                            "displayName": device.display_name,
                            "placeId": device.place_id,
                            "tags": device.tags,
                        },
                    )
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    errors.append((device.display_name, str(e)))
                
                progress.update(task, advance=1)
            
            progress.update(task, description=f"{len(devices)}/{len(devices)}")
        
        # Display summary
        console.print(format_success(f"Activated {success_count} of {len(devices)} devices."))
        
        if error_count > 0:
            console.print(format_warning(f"Failed to activate {error_count} devices:"))
            
            # Create table of errors
            table = create_table(
                title="Activation Errors",
                columns=["Device", "Error"],
                rows=errors,
            )
            console.print(table)
    
    except Exception as e:
        console.print(format_error(f"Failed to process CSV file: {str(e)}"))
        sys.exit(1)


@devices_group.command(name="create-meeting", help="Create a meeting room device and workspace.")
@click.argument("display_name", required=True)
@click.argument("org_id", required=True)
@click.option(
    "--capacity",
    type=int,
    default=10,
    help="Capacity of the workspace.",
    show_default=True,
)
@click.option(
    "--location-id",
    required=True,
    help="ID of the location where the workspace will be created.",
)
@click.option(
    "--type",
    "workspace_type",
    type=click.Choice(["meetingRoom", "huddle", "focus", "desk", "other"]),
    default="meetingRoom",
    help="Type of workspace.",
    show_default=True,
)
@click.option(
    "--calling",
    type=str,
    help="JSON string for calling configuration.",
)
@click.option(
    "--calendar",
    type=str,
    help="JSON string for calendar configuration.",
)
@click.option(
    "--hotdesking-status",
    type=click.Choice(["on", "off"]),
    default="off",
    help="Hotdesking status.",
    show_default=True,
)
@click.option(
    "--device-hosted-meetings",
    type=str,
    help="JSON string for device hosted meetings configuration.",
)
@click.option(
    "--output-csv",
    type=click.Path(),
    help="Path to save the activation results to a CSV file.",
)
@click.pass_context
def create_meeting_device(
    ctx: click.Context,
    display_name: str,
    org_id: str,
    capacity: int = 10,
    location_id: str = None,
    workspace_type: str = "meetingRoom",
    calling: Optional[str] = None,
    calendar: Optional[str] = None,
    hotdesking_status: str = "off",
    device_hosted_meetings: Optional[str] = None,
    output_csv: Optional[str] = None,
) -> None:
    """
    Create a meeting room device and workspace.
    
    Args:
        ctx: Click context.
        display_name: Display name for the workspace and device.
        org_id: Organization ID.
        capacity: Capacity of the workspace.
        location_id: ID of the location where the workspace will be created.
        workspace_type: Type of workspace.
        calling: JSON string for calling configuration.
        calendar: JSON string for calendar configuration.
        hotdesking_status: Hotdesking status.
        device_hosted_meetings: JSON string for device hosted meetings configuration.
        output_csv: Path to save the activation results to a CSV file.
    """
    debug = ctx.obj.get("DEBUG", False)
    
    # Parse JSON strings
    calling_config = None
    calendar_config = None
    device_hosted_meetings_config = None
    
    if calling:
        try:
            calling_config = json.loads(calling)
        except json.JSONDecodeError:
            console.print(format_error("Invalid JSON for calling configuration."))
            sys.exit(1)
    
    if calendar:
        try:
            calendar_config = json.loads(calendar)
        except json.JSONDecodeError:
            console.print(format_error("Invalid JSON for calendar configuration."))
            sys.exit(1)
    
    if device_hosted_meetings:
        try:
            device_hosted_meetings_config = json.loads(device_hosted_meetings)
        except json.JSONDecodeError:
            console.print(format_error("Invalid JSON for device hosted meetings configuration."))
            sys.exit(1)
    
    try:
        api = WebexAPI()
        
        # Step 1: Create workspace
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Creating workspace...[/bold blue]"),
            console=console,
        ) as progress:
            progress.add_task("create", total=None)
            
            workspace_payload = {
                "displayName": display_name,
                "orgId": org_id,
                "capacity": capacity,
                "type": workspace_type,
                "calling": calling_config,
                "calendar": calendar_config,
                "hotdeskingStatus": hotdesking_status,
                "deviceHostedMeetings": device_hosted_meetings_config,
                "workspaceLocationId": location_id
            }
            
            # Remove None values
            workspace_payload = {k: v for k, v in workspace_payload.items() if v is not None}
            
            workspace_response = api.post("workspaces", workspace_payload)
            workspace_id = workspace_response.get("id")
        
        if not workspace_id:
            console.print(format_error("Failed to create workspace: No workspace ID returned."))
            sys.exit(1)
        
        # Step 2: Assign device to workspace and get activation code
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Generating activation code...[/bold blue]"),
            console=console,
        ) as progress:
            progress.add_task("activate", total=None)
            
            activation_response = api.post(
                f"devices/activationCode?orgId={org_id}",
                {"workspaceId": workspace_id}
            )
        
        activation_code = activation_response.get("code")
        expiry_time = activation_response.get("expiryTime")
        
        if not activation_code:
            console.print(format_error("Failed to generate activation code."))
            sys.exit(1)
        
        # Display results
        result = {
            "Workspace Name": display_name,
            "Workspace ID": workspace_id,
            "Activation Code": activation_code,
            "Expiry Time": expiry_time
        }
        
        console.print(format_success(f"Successfully created workspace and generated activation code."))
        console.print(format_dict_as_table(result, title="Meeting Device Creation Results"))
        
        # Save to CSV if requested
        if output_csv:
            with open(output_csv, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=result.keys())
                writer.writeheader()
                writer.writerow(result)
            console.print(format_success(f"Results saved to {output_csv}"))
    
    except Exception as e:
        console.print(format_error(f"Failed to create meeting device: {str(e)}"))
        sys.exit(1)


@devices_group.command(name="create-meeting-batch", help="Create multiple meeting room devices and workspaces from a CSV file.")
@click.argument("csv_file", type=click.Path(exists=True), required=True)
@click.option(
    "--output-csv",
    type=click.Path(),
    help="Path to save the activation results to a CSV file.",
)
@click.pass_context
def create_meeting_devices_batch(
    ctx: click.Context,
    csv_file: str,
    output_csv: Optional[str] = None,
) -> None:
    """
    Create multiple meeting room devices and workspaces from a CSV file.
    
    The CSV file should have the following columns:
    - displayName: Display name for the workspace and device.
    - orgId: Organization ID.
    - LocationID: ID of the location where the workspace will be created.
    - capacity: (Optional) Capacity of the workspace.
    - type: (Optional) Type of workspace.
    - calling: (Optional) JSON string for calling configuration.
    - calendar: (Optional) JSON string for calendar configuration.
    - hotdeskingStatus: (Optional) Hotdesking status.
    - deviceHostedMeetings: (Optional) JSON string for device hosted meetings configuration.
    
    Args:
        ctx: Click context.
        csv_file: Path to CSV file with device information.
        output_csv: Path to save the activation results to a CSV file.
    """
    debug = ctx.obj.get("DEBUG", False)
    
    try:
        # Read CSV file
        import pandas as pd
        data = pd.read_csv(csv_file)
        results = []
        
        api = WebexAPI()
        
        success_count = 0
        error_count = 0
        errors = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Creating meeting devices...[/bold blue] {task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("", total=len(data), description=f"0/{len(data)}")
            
            for i, row in data.iterrows():
                progress.update(task, description=f"{i}/{len(data)}")
                
                try:
                    # Extract values from row
                    display_name = row["displayName"]
                    org_id = row["orgId"]
                    location_id = row["LocationID"]
                    capacity = row.get("capacity", 10)
                    workspace_type = row.get("type", "meetingRoom")
                    
                    # Parse JSON fields
                    calling_config = json.loads(row["calling"]) if pd.notna(row.get("calling")) else None
                    calendar_config = json.loads(row["calendar"]) if pd.notna(row.get("calendar")) else None
                    hotdesking_status = row.get("hotdeskingStatus", "off")
                    device_hosted_meetings_config = json.loads(row["deviceHostedMeetings"]) if pd.notna(row.get("deviceHostedMeetings")) else None
                    
                    # Step 1: Create workspace
                    workspace_payload = {
                        "displayName": display_name,
                        "orgId": org_id,
                        "capacity": capacity,
                        "type": workspace_type,
                        "calling": calling_config,
                        "calendar": calendar_config,
                        "hotdeskingStatus": hotdesking_status,
                        "deviceHostedMeetings": device_hosted_meetings_config,
                        "workspaceLocationId": location_id
                    }
                    
                    # Remove None values
                    workspace_payload = {k: v for k, v in workspace_payload.items() if v is not None}
                    
                    workspace_response = api.post("workspaces", workspace_payload)
                    workspace_id = workspace_response.get("id")
                    
                    if not workspace_id:
                        raise ValueError("No workspace ID returned.")
                    
                    # Step 2: Assign device to workspace and get activation code
                    activation_response = api.post(
                        f"devices/activationCode?orgId={org_id}",
                        {"workspaceId": workspace_id}
                    )
                    
                    activation_code = activation_response.get("code")
                    expiry_time = activation_response.get("expiryTime")
                    
                    if not activation_code:
                        raise ValueError("Failed to generate activation code.")
                    
                    # Add to results
                    results.append({
                        "displayName": display_name,
                        "workspaceId": workspace_id,
                        "activationCode": activation_code,
                        "expiryTime": expiry_time
                    })
                    
                    success_count += 1
                
                except Exception as e:
                    error_count += 1
                    errors.append((row.get("displayName", f"Row {i+1}"), str(e)))
                
                progress.update(task, advance=1)
            
            progress.update(task, description=f"{len(data)}/{len(data)}")
        
        # Display summary
        console.print(format_success(f"Created {success_count} of {len(data)} meeting devices."))
        
        if error_count > 0:
            console.print(format_warning(f"Failed to create {error_count} meeting devices:"))
            
            # Create table of errors
            table = create_table(
                title="Creation Errors",
                columns=["Device", "Error"],
                rows=errors,
            )
            console.print(table)
        
        # Save results to CSV if requested
        if output_csv and results:
            results_df = pd.DataFrame(results)
            results_df.to_csv(output_csv, index=False)
            console.print(format_success(f"Results saved to {output_csv}"))
    
    except Exception as e:
        console.print(format_error(f"Failed to process CSV file: {str(e)}"))
        sys.exit(1)


@devices_group.command(name="list", help="List Webex devices.")
@click.option(
    "--display-name",
    help="Filter devices by display name (supports partial matching).",
)
@click.option(
    "--type",
    "device_type",
    type=click.Choice([t.value for t in DeviceType]),
    help="Filter devices by type.",
)
@click.option(
    "--place-id",
    help="Filter devices by place ID.",
)
@click.option(
    "--tag",
    help="Filter devices by tag.",
)
@click.option(
    "--limit",
    type=int,
    default=100,
    help="Maximum number of devices to return.",
    show_default=True,
)
@click.pass_context
def list_devices(
    ctx: click.Context,
    display_name: Optional[str] = None,
    device_type: Optional[str] = None,
    place_id: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 100,
) -> None:
    """
    List Webex devices with optional filtering.
    
    Args:
        ctx: Click context.
        display_name: Filter devices by display name (supports partial matching).
        device_type: Filter devices by type.
        place_id: Filter devices by place ID.
        tag: Filter devices by tag.
        limit: Maximum number of devices to return.
    """
    debug = ctx.obj.get("DEBUG", False)
    
    try:
        api = WebexAPI()
        
        # Build query parameters
        params = {"max": limit}
        if display_name:
            params["displayName"] = display_name
        if device_type:
            params["type"] = device_type
        if place_id:
            params["placeId"] = place_id
        if tag:
            params["tag"] = tag
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Fetching devices...[/bold blue]"),
            console=console,
        ) as progress:
            progress.add_task("fetch", total=None)
            
            # Make API call to list devices
            devices = api.get_all_pages("devices", params)
        
        if not devices:
            console.print(format_warning("No devices found matching the criteria."))
            return
        
        # Create table of devices
        rows = []
        for device in devices:
            rows.append([
                device.get("displayName", ""),
                device.get("type", ""),
                device.get("product", ""),
                device.get("connectionStatus", ""),
                device.get("id", ""),
            ])
        
        table = create_table(
            title=f"Webex Devices ({len(devices)})",
            columns=["Display Name", "Type", "Product", "Status", "ID"],
            rows=rows,
        )
        console.print(table)
        
        # Display additional information in debug mode
        if debug:
            console.print(f"Total devices: {len(devices)}")
            console.print(f"Query parameters: {params}")
    
    except Exception as e:
        console.print(format_error(f"Failed to list devices: {str(e)}"))
        sys.exit(1)
