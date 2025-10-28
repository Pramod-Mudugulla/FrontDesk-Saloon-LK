import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

from livekit.agents import function_tool, RunContext, get_job_context
from db import get_session
from db.repository import (
    init_db,
    create_or_get_customer,
    create_call_session,
    create_help_request,
)

@function_tool
async def transfer_to_human(ctx: RunContext):
    """Simulated transfer to human supervisor"""
    logger = logging.getLogger("phone-assistant")
    job_ctx = get_job_context()
    if job_ctx is None:
        logger.error("🔴 Job context not found")
        return 'error'

    # Simulate capturing the last user question
    last_question = ctx.transcript if hasattr(ctx, 'transcript') else "Unknown question"
    room_name = getattr(getattr(job_ctx, "room", None), "name", "mock_room")


    # Ensure DB is initialized (idempotent)
    try:
        init_db()
    except Exception as e:
        logger.error(f"DB init failed: {e}")

    # Persist help request
    with get_session() as session:
        customer = create_or_get_customer(
            session,
            external_id=None,
            display_name=None,
            phone_number=None,
        )
        call_session = create_call_session(session, room_name=room_name, customer=customer)
        help_request = create_help_request(session, call_session=call_session, customer=customer, question=last_question)
        help_request_id = help_request.id

    # Simulate notifying a human supervisor
    logger.info(f"[SUPERVISOR ALERT] Room {room_name} asked: {last_question}")
    logger.info(f"Help request created with id={help_request_id} and status=pending")

    return 'simulated_transfer'

@function_tool
async def end_call(ctx: RunContext):
    """Simulated end call"""
    logger = logging.getLogger('phone-assistant')
    job_ctx = get_job_context()
    room_name = getattr(job_ctx, 'room', {}).name if hasattr(job_ctx, 'room') else "mock_room"

    logger.info(f"Ending call for room {room_name}")

    # In simulation, just log instead of deleting real LiveKit rooms
    logger.info(f"🟢Successfully ended the call for room {room_name}")
    return 'ended'














# ---------------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------


# import logging
# from livekit import api
# from livekit.agents import function_tool, RunContext, get_job_context, job

# @function_tool
# async def transfer_to_human(ctx: RunContext):
#   """Transfer to specialist. Call obnly after confirming the users consent to be transferred"""
#   logger = logging.getLogger("phone-assistant")
#   job_ctx = get_job_context()
#   if job_ctx is None:
#     logger.error("🔴 Job context not found")
#     return 'error'

#   transfer_to = "tel: +918074637853"  # ☑️ remember we'll try setting multiple if we have time

#   #finding of sip participants ( ☑️ remember dont know from where yet, we'll see later)
#   sip_participant = None
#   for participant in job_ctx.room.remote_participants.values():
#       if participant.identity.startswith('sip'):
#         sip_participant = participant
#         break
#   if sip_participant is None:
#     logger.error("No SIP participant found")
#     return 'error'

#   logger.info(f'Transferring call for participant {sip_participant.identity} to {transfer_to}')

#   try:
#     await job_ctx.api.sip.transfer_sip_participant(
#       api.TransferSIPParticipantRequest(
#         room_name = job_ctx.room.name,
#         participant_identity = sip_participant.identity,
#         transfer_to = transfer_to,
#         play_dialtone=True
#       )
#     )
#     logger.info(f'🟢Successfull transferred participant {sip_participant.identity} to {transfer_to}')
#     return 'transferred'
#   except Exception as e:
#     logger.error(f'🔴Failed to transfer call: {e}', exc_info=True)
#     return 'error'

# @function_tool
# async def end_call(ctx: RunContext):
#   """End call. If the user isn't intersted, expressed disinterest, or wants to end the call"""
#   logger = logging.getLogger('phone-assistant')

#   job_ctx = get_job_context()
#   if job_ctx is None:
#     logger.error('🔴Failed to get job context')
#     return 'error'
  
#   logger.info(f'Ending call for room {job_ctx.room.name}')

#   try:
#     await job_ctx.api.room.delete_room(
#       api.DeleteRoomRequest(
#         room = job_ctx.room.name,
#       )
#     )
#     logger.info(f'🟢Successfully ended the call for room {job_ctx.room.name}')
#     return 'ended'
#   except Exception as e:
#     logger.error(f'Failed to end the call: {e}', exc_info=True)
#     return 'error'
