import adsk.core
import os
import math
from ...lib import fusionAddInUtils as futil
from ... import config
import traceback

app = adsk.core.Application.get()
ui = app.userInterface

# Get the active design
product = app.activeProduct
design = adsk.fusion.Design.cast(product)
rootComp = design.rootComponent


# TODO *** Specify the command identity information. ***
CMD_ID = f"{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdDialog"
CMD_NAME = "Reorient Component"
CMD_Description = "Reorient the selected component while maintaining the same orientation of the bodies inside."

# Specify that the command will be promoted to the panel.
IS_PROMOTED = True

# TODO *** Define the location where the command button will be created. ***
# This is done by specifying the workspace, the tab, and the panel, and the
# command it will be inserted beside. Not providing the command to position it
# will insert it at the end.
WORKSPACE_ID = "FusionSolidEnvironment"
PANEL_ID = "SolidScriptsAddinsPanel"
COMMAND_BESIDE_ID = "ScriptsManagerCommand"

# Resource location for command icons, here we assume a sub folder in this directory named "resources".
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "")

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []

# Executed when add-in is run.
def start():
    # Create a command Definition.
    cmd_def = ui.commandDefinitions.addButtonDefinition(
        CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER
    )

    # Define an event handler for the command created event. It will be called when the button is clicked.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # ******** Add a button into the UI so the user can run the command. ********
    # Get the target workspace the button will be created in.
    workspace = ui.workspaces.itemById(WORKSPACE_ID)

    # Get the panel the button will be created in.
    panel = workspace.toolbarPanels.itemById(PANEL_ID)

    # Create the button command control in the UI after the specified existing command.
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)

    # Specify if the command is promoted to the main toolbar.
    control.isPromoted = IS_PROMOTED


# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()


# Function that is called when a user clicks the corresponding button in the UI.
# This defines the contents of the command dialog and connects to the command related events.
def command_created(args: adsk.core.CommandCreatedEventArgs):
    # General logging for debug.
    futil.log(f"{CMD_NAME} Command Created Event")

    # https://help.autodesk.com/view/fusion360/ENU/?contextId=CommandInputs
    inputs = args.command.commandInputs

    # TODO Define the dialog for your command by adding different inputs to the command.

    selectionComponentInput = inputs.addSelectionInput("selectionComponentInput", "Select Component", "Select Component")
    selectionComponentInput.addSelectionFilter("Occurrences")
    selectionComponentInput.setSelectionLimits(1, 1)

    selectionFaceInput = inputs.addSelectionInput(
        "selectionFaceInput", "Select Face", "Select Face"
    )
    selectionFaceInput.addSelectionFilter("PlanarFaces")
    selectionFaceInput.setSelectionLimits(1, 1)

    originMatrix = adsk.core.Matrix3D.create()
    triadInput = inputs.addTriadCommandInput("triadInput", originMatrix)
    triadInput.hideAll()


    # TODO Connect to the events that are needed by this command.
    futil.add_handler(
        args.command.execute, command_execute, local_handlers=local_handlers
    )
    futil.add_handler(
        args.command.inputChanged, command_input_changed, local_handlers=local_handlers
    )
    # futil.add_handler(
    #     args.command.executePreview, command_preview, local_handlers=local_handlers
    # )
    futil.add_handler(
        args.command.validateInputs,
        command_validate_input,
        local_handlers=local_handlers,
    )
    futil.add_handler(
        args.command.destroy, command_destroy, local_handlers=local_handlers
    )


# This event handler is called when the user clicks the OK button in the command dialog or
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f"{CMD_NAME} Command Execute Event")
    inputs = args.command.commandInputs

    # TODO ******************************** Your code here ********************************

# This event handler is called when the command needs to compute a new preview in the graphics window.
def command_preview(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f"{CMD_NAME} Command Preview Event")
    inputs = args.command.commandInputs

occurrence_original_transform = None
last_selected_occurrence = None

# This event handler is called when the user changes anything in the command dialog
# allowing you to modify values of other inputs based on that change.
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    inputs = args.inputs

    global occurrence_original_transform, last_selected_occurrence

    selectionComponentInput = inputs.itemById("selectionComponentInput")
    selectionFaceInput = inputs.itemById("selectionFaceInput")
    triadInput = inputs.itemById("triadInput")

    if changed_input.id == 'selectionFaceInput':
        if selectionFaceInput.selectionCount > 0:
            selectedFace = selectionFaceInput.selection(0).entity
            body = selectedFace.body
            component = body.parentComponent
            occurrenceList = rootComp.allOccurrencesByComponent(component)
            occurrence = occurrenceList.itemByName(f'{component.name}:1')

            if selectionComponentInput.selectionCount == 0:
                selectionComponentInput.addSelection(occurrence)

                occurrence = selectionComponentInput.selection(0).entity
                occurrence_original_transform = occurrence.transform2.copy()
                last_selected_occurrence = occurrence

                futil.log(f'original transform >>> {[round(e, 6) for e in occurrence_original_transform.asArray()]}')

            else:
                futil.log('Occurrence has been selected')

            target_origin = adsk.core.Point3D.create(0, 0, 0)       # Point3D
            target_normal = adsk.core.Vector3D.create(0, 0, -1)     # Vector3D
            face_centroid = selectedFace.centroid                   # Point3D
            face_evaluator = selectedFace.evaluator
            (returnValue, face_normal) = face_evaluator.getNormalAtPoint(face_centroid)

            futil.log(f'Evaluator >>> returned value: {returnValue} | normal vector: {[round(e, 6) for e in face_normal.asArray()]}')
        
            identity_matrix = adsk.core.Matrix3D.create()
            occurrence.transform2 = identity_matrix
            selectionComponentInput.addSelection(occurrence)
        else:
            futil.log('No selection')
            identity_matrix = adsk.core.Matrix3D.create()
            last_selected_occurrence.transform2 = identity_matrix
            selectionComponentInput.addSelection(occurrence)
            selectionFaceInput.addSelection(selectedFace)

    elif changed_input.id == 'selectionComponentInput':
        if selectionComponentInput.selectionCount > 0:
            occurrence = selectionComponentInput.selection(0).entity
            occurrence_original_transform = occurrence.transform2.copy()
            last_selected_occurrence = occurrence

            futil.log(f'original transform >>> {[round(e, 6) for e in occurrence_original_transform.asArray()]}')

            identity_matrix = adsk.core.Matrix3D.create()
            occurrence.transform2 = identity_matrix

            selectionComponentInput.addSelection(occurrence)
        else:
            futil.log('Component is not selected')
            if last_selected_occurrence and occurrence_original_transform:
                last_selected_occurrence.transform2 = occurrence_original_transform

                # clear the global variables
                occurrence_original_transform = None
                last_selected_occurrence = None

    elif changed_input.id == 'triadInput':
        # futil.log(f'current triad transform: {[round(e, 6) for e in triadInput.transform.asArray()]}')
        pass

    # General logging for debug.
    futil.log(
        f"{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}"
    )


# This event handler is called when the user interacts with any of the inputs in the dialog
# which allows you to verify that all of the inputs are valid and enables the OK button.
def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    # General logging for debug.
    # futil.log(f"{CMD_NAME} Validate Input Event")

    inputs = args.inputs

    # Verify the validity of the input values. This controls if the OK button is enabled or not.
    # valueInput = inputs.itemById("value_input")
    # if valueInput.value >= 0:
    #     args.areInputsValid = True
    # else:
    #     args.areInputsValid = False


def command_destroy(args: adsk.core.CommandEventArgs):
    # This event handler is called when the command terminates.
    # General logging for debug.
    futil.log(f"{CMD_NAME} Command Destroy Event")

    global local_handlers
    local_handlers = []
