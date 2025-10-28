import os

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import noise_cancellation, silero
from prompt import AGENT_INSTRUCTIONS, SESSION_INSTRUCTIONS
from tool import end_call, transfer_to_human

load_dotenv(".env.local")


class Assistant(Agent):
    def __init__(self):
        super().__init__(
            instructions=f"{AGENT_INSTRUCTIONS}, {SESSION_INSTRUCTIONS}",
            tools = [end_call, transfer_to_human]
        )

async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        stt = "deepgram/nova-3:en",
        llm = "google/gemini-2.5-flash",
        tts = "elevenlabs/eleven_flash_v2:cgSgspJ2msm6clMCkdW9",
        vad = silero.VAD.load(),
    )

    await session.start(
        room = ctx.room,
        agent = Assistant(),
        room_input_options = RoomInputOptions(
            noise_cancellation = noise_cancellation.BVC(),
        ), 
    )

    await session.generate_reply(
        instructions=SESSION_INSTRUCTIONS,
    )

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(
        entrypoint_fnc=entrypoint,
        agent_name='Pramod-call-screener'
        
        ))