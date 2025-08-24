import adsk.core
import adsk.fusion
import os
import math
from ...lib import fusionAddInUtils as futil
from ... import config
import traceback

app = adsk.core.Application.get()
ui = app.userInterface

# global variables *********************************************
body_transform_matrix = adsk.core.Matrix3D.create()
original_occ_transform = adsk.core.Matrix3D.create()
selected_body = None
is_valid = False

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

    # selection input for selecting planar face
    select_face_input = inputs.addSelectionInput("selectFaceInput", "Select Face", "Select Face")
    select_face_input.addSelectionFilter("PlanarFaces")
    select_face_input.setSelectionLimits(1, 1)

    initial_matrix = adsk.core.Matrix3D.create()
    triad_input = inputs.addTriadCommandInput('triadInput', initial_matrix)
    triad_input.hideAll()

    errorTextInput = inputs.addTextBoxCommandInput('errorTextInput', 'Log', '', 3, True)
    errorTextInput.isFullWidth = True

    # TODO Connect to the events that are needed by this command.
    futil.add_handler(
        args.command.execute, command_execute, local_handlers=local_handlers
    )
    futil.add_handler(
        args.command.inputChanged, command_input_changed, local_handlers=local_handlers
    )
    futil.add_handler(
        args.command.executePreview, command_preview, local_handlers=local_handlers
    )
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

    product = app.activeProduct    
    design = adsk.fusion.Design.cast(product)    
    root_comp = design.rootComponent    
    features = root_comp.features    
    
    global selected_body, body_transform_matrix

    # TODO ******************************** Your code here ********************************

    # Find the occurrence that contains the selected_body (A)
    selected_occurrence = None
    for occ in root_comp.allOccurrences:
        for body in occ.bRepBodies:
            if body == selected_body:
                selected_occurrence = occ
                selected_occurrence.isGrounded = False
                selected_occurrence.isGroundToParent = False
                break
        if selected_occurrence:
            break
    
    occ_init_transform = selected_occurrence.transform2.copy()
    inverse_occ_init_transform = occ_init_transform.copy()
    inverse_occ_init_transform.invert()

    selected_occurrence.transform2 = adsk.core.Matrix3D.create()

    # check if there is transformation
    if not body_transform_matrix.isEqualTo(adsk.core.Matrix3D.create()):
        body_collection = adsk.core.ObjectCollection.create()
        body_collection.add(selected_body)
        moveFeats = features.moveFeatures
        moveFeatureInput = moveFeats.createInput2(body_collection)
        moveFeatureInput.defineAsFreeMove(body_transform_matrix)
        moveFeats.add(moveFeatureInput)

    selected_occurrence.transform2 = occ_init_transform
    
    # get the inverse of body's transform (IBT)
    inverse_body_transform = body_transform_matrix.copy()
    inverse_body_transform.invert()

    # apply the inverse of body's transform to all occurrences referencing component
    component = selected_body.parentComponent
    occurrences = root_comp.allOccurrencesByComponent(component)

    for i in range(occurrences.count):
        occ = occurrences.item(i)
        occ_transform = occ.transform2.copy()

        # post-multiply. get local transformation in global form
        transform = inverse_body_transform.copy()
        transform.transformBy(occ_transform)

        occ.transform2 = transform


# This event handler is called when the command needs to compute a new preview in the graphics window.
def command_preview(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f"{CMD_NAME} Command Preview Event")
    inputs = args.command.commandInputs

    product = app.activeProduct
    design = adsk.fusion.Design.cast(product)
    root_comp = design.rootComponent
    features = root_comp.features

    global body_transform_matrix, selected_body, is_valid
    
    # Grabing inputs **********************************************************************

    select_face_input = adsk.core.SelectionCommandInput.cast(inputs.itemById('selectFaceInput'))
    triad_input = adsk.core.TriadCommandInput.cast(inputs.itemById('triadInput'))

    # TODO ******************************** Your code here ********************************

    if not is_valid:
        return

    count = select_face_input.selectionCount
    if count:        
        face = select_face_input.selection(0).entity
        face = adsk.fusion.BRepFace.cast(face)
        
        body = face.body
        body_collection = adsk.core.ObjectCollection.create()
        body_collection.add(body)
        selected_body = body

        root_comp.isOriginFolderLightBulbOn = True
        
        # Find the occurrence that contains the selected_body
        selected_occurrence = None
        for occ in root_comp.allOccurrences:
            for body in occ.bRepBodies:
                if body == selected_body:
                    selected_occurrence = occ
                    selected_occurrence.transform2 = adsk.core.Matrix3D.create()
                    selected_occurrence.isIsolated = True
                    break
            if selected_occurrence:
                break
        
        face_evaluator = face.evaluator
        face_center = face.centroid
        (returnValue, face_normal) = face_evaluator.getNormalAtPoint(face_center)

        face_center = adsk.core.Point3D.cast(face_center)
        face_normal = adsk.core.Vector3D.cast(face_normal)

        target_origin = adsk.core.Point3D.create(0, 0, 0)
        target_normal = adsk.core.Vector3D.create(0, 0, -1)

        transform_matrix = adsk.core.Matrix3D.create()

        # Translate the face's point to the target origin
        translation_vector = face_center.vectorTo(target_origin)
        transform_matrix.translation = translation_vector

        # Create a rotation matrix and combine with the translation
        # Note: This is a simplified rotation. For complex alignments,
        # you might need to consider multiple rotations or a more robust alignment algorithm.
        # For a planar face, aligning its normal and then translating its point usually works.
        rotation_matrix = adsk.core.Matrix3D.create()
        rotation_matrix.setToRotateTo(face_normal, target_normal)

        triad_rotation_matrix = triad_input.transform.copy()

        # Combine translation and rotation (order matters: rotate then translate)
        transform_matrix.transformBy(rotation_matrix)
        transform_matrix.transformBy(triad_rotation_matrix)

        body_transform_matrix = transform_matrix

        # check if there is transformation and move if not
        if not transform_matrix.isEqualTo(adsk.core.Matrix3D.create()):
            moveFeats = features.moveFeatures
            moveFeatureInput = moveFeats.createInput2(body_collection)
            moveFeatureInput.defineAsFreeMove(transform_matrix)
            moveFeats.add(moveFeatureInput)

    else:
        futil.log(f'not selected')
        body_transform_matrix = adsk.core.Matrix3D.create()
        selected_body = None
        root_comp.isOriginFolderLightBulbOn = False


# This event handler is called when the user changes anything in the command dialog
# allowing you to modify values of other inputs based on that change.
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    inputs = args.inputs

    product = app.activeProduct
    design = adsk.fusion.Design.cast(product)
    root_comp = design.rootComponent

    global is_valid

    # General logging for debug.
    futil.log(f"{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}")

    # Grabing inputs **********************************************************************

    select_face_input = adsk.core.SelectionCommandInput.cast(inputs.itemById('selectFaceInput'))
    triad_input = adsk.core.TriadCommandInput.cast(inputs.itemById('triadInput'))
    errorTextInput = adsk.core.TextBoxCommandInput.cast(inputs.itemById('errorTextInput'))

    # TODO ******************************** Your code here ********************************

    if select_face_input.selectionCount:
        face = select_face_input.selection(0).entity
        face = adsk.fusion.BRepFace.cast(face)
        body = face.body
        parent_component = body.parentComponent

        comp_child_occs = parent_component.occurrences
        comp_bodies = parent_component.bRepBodies
        comp_is_root = parent_component == root_comp

        futil.log(f'comp_child_occs >>> {comp_child_occs}')
        futil.log(f'comp_bodies >>> {comp_bodies}')
        futil.log(f'comp_is_root >>> {comp_is_root}')

        if comp_child_occs.count > 0:
            errorTextInput.text = 'ERROR: This component is an assembly.'
            is_valid = False
        elif comp_bodies.count > 1:
            errorTextInput.text = 'ERROR: This component contains more than one body.'
            is_valid = False
        elif comp_is_root:
            errorTextInput.text = 'ERROR: Cannot move root component.'
            is_valid = False
        else:
            is_valid = True

            if not triad_input.isZRotationVisible:
                triad_input.isZRotationVisible = True
    else:
        triad_input.isZRotationVisible = False


# This event handler is called when the user interacts with any of the inputs in the dialog
# which allows you to verify that all of the inputs are valid and enables the OK button.
def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    # General logging for debug.
    futil.log(f"{CMD_NAME} Validate Input Event")

    inputs = args.inputs

    # Grabing inputs **********************************************************************

    select_face_input = adsk.core.SelectionCommandInput.cast(inputs.itemById('selectFaceInput'))
    errorTextInput = adsk.core.TextBoxCommandInput.cast(inputs.itemById('errorTextInput'))

    # TODO ******************************** Your code here ********************************
    
    if select_face_input.selectionCount:
        args.areInputsValid = True
    else:
        args.areInputsValid = False
        errorTextInput.text = 'No face selected.'


def command_destroy(args: adsk.core.CommandEventArgs):
    # This event handler is called when the command terminates.
    # General logging for debug.
    futil.log(f"{CMD_NAME} Command Destroy Event")

    global local_handlers
    local_handlers = []