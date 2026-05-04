
import discord
from discord.ext import commands
import random
import json
import asyncio
import os
import time

# ════════════════════════════════
# 🔐 TOKEN (usa variable de entorno)
# Ejecuta: export DISCORD_TOKEN="tu_token_aquí"
# O crea un archivo .env con: DISCORD_TOKEN=tu_token_aquí
# ════════════════════════════════


TOKEN = "MTQ5OTM3MjQ2NzAzMzA4Mzk0NA.GkeHVJ.fzfXx8xn2rY1QtlRcd-9z0wXSj798oMGsyt6E4"
if not TOKEN:
    raise ValueError("❌ No se encontró DISCORD_TOKEN en las variables de entorno.")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)

COLOR = discord.Color.from_rgb(0, 180, 80)

# ════════════════════════════════
# 💾 BASE DE DATOS
# ════════════════════════════════

db = {}
db_lock = asyncio.Lock()

def cargar_db():
    global db
    if os.path.exists("economia.json"):
        with open("economia.json", "r") as f:
            db = json.load(f)

async def guardar_db():
    async with db_lock:
        with open("economia.json", "w") as f:
            json.dump(db, f, indent=4)

def get_user(uid):
    uid = str(uid)
    if uid not in db:
        db[uid] = {
            "balance": 1000,
            "banco": 0,
            "last_daily": 0,
            "last_trabajo": 0
        }
    # Migrar usuarios viejos sin last_trabajo
    if "last_trabajo" not in db[uid]:
        db[uid]["last_trabajo"] = 0
    return db[uid]

# ════════════════════════════════
# ❌ MANEJO DE ERRORES GLOBAL
# ════════════════════════════════

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        minutos = int(error.retry_after // 60)
        segundos = int(error.retry_after % 60)
        await ctx.send(f"⏳ Espera **{minutos}m {segundos}s** para usar ese comando.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Falta un argumento. Usa `!help` para ver cómo usarlo.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Argumento inválido. Asegúrate de ingresar un número entero.")
    else:
        raise error

# ════════════════════════════════
# 📜 HELP
# ════════════════════════════════

@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="🎰 CASINO BOT",
        description="Bienvenido al casino 💎",
        color=COLOR
    )
    embed.add_field(
        name="💰 Economía",
        value=(
            "`!balance` — Ver tu saldo\n"
            "`!trabajar` — Ganar dinero (cooldown 1h)\n"
            "`!daily` — Recompensa diaria\n"
            "`!depositar <cantidad>` — Depositar al banco\n"
            "`!retirar <cantidad>` — Retirar del banco\n"
            "`!ranking` — Top 5 más ricos"
        ),
        inline=False
    )
    embed.add_field(
        name="🎰 Juegos",
        value=(
            "`!slots <apuesta>` — Máquina tragamonedas\n"
            "`!ruleta <apuesta> <rojo/negro/verde>` — Ruleta\n"
            "`!bj <apuesta>` — Blackjack interactivo\n"
            "`!coinflip <apuesta> <cara/cruz>` — Lanzar moneda\n"
            "`!dados <apuesta> <número 2-12>` — Lanzar dados"
        ),
        inline=False
    )
    embed.set_footer(text="💡 El banco protege tu dinero de pérdidas en juegos")
    await ctx.send(embed=embed)

# ════════════════════════════════
# 💰 ECONOMÍA
# ════════════════════════════════

@bot.command()
async def balance(ctx):
    user = get_user(ctx.author.id)
    total = user["balance"] + user["banco"]

    embed = discord.Embed(title=f"💰 Balance de {ctx.author.display_name}", color=COLOR)
    embed.add_field(name="👛 Cartera", value=f"**${user['balance']:,}**", inline=True)
    embed.add_field(name="🏦 Banco", value=f"**${user['banco']:,}**", inline=True)
    embed.add_field(name="💎 Total", value=f"**${total:,}**", inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def trabajar(ctx):
    user = get_user(ctx.author.id)

    ahora = int(time.time())
    cooldown = 3600  # 1 hora

    tiempo_restante = cooldown - (ahora - user["last_trabajo"])
    if tiempo_restante > 0:
        minutos = tiempo_restante // 60
        segundos = tiempo_restante % 60
        return await ctx.send(f"⏳ Debes esperar **{minutos}m {segundos}s** para volver a trabajar.")

    trabajos = [
        ("👨‍💻 Programaste una app", random.randint(300, 700)),
        ("🍕 Repartiste pizzas", random.randint(200, 400)),
        ("🎸 Tocaste en la calle", random.randint(100, 350)),
        ("📦 Trabajaste en el almacén", random.randint(250, 500)),
        ("🚗 Fuiste conductor de Uber", random.randint(200, 600)),
        ("🧹 Limpiaste oficinas", random.randint(150, 300)),
        ("📊 Hiciste consultoría", random.randint(400, 800)),
    ]
    descripcion, ganancia = random.choice(trabajos)

    user["balance"] += ganancia
    user["last_trabajo"] = ahora
    await guardar_db()

    embed = discord.Embed(title="💼 Trabajo completado", color=COLOR)
    embed.add_field(name=descripcion, value=f"Ganaste **${ganancia:,}**")
    embed.set_footer(text="Podrás trabajar de nuevo en 1 hora")
    await ctx.send(embed=embed)

@bot.command()
async def daily(ctx):
    user = get_user(ctx.author.id)

    ahora = int(time.time())

    if ahora - user["last_daily"] < 86400:
        tiempo_restante = 86400 - (ahora - user["last_daily"])
        horas = tiempo_restante // 3600
        minutos = (tiempo_restante % 3600) // 60
        return await ctx.send(f"⏳ Ya reclamaste tu daily. Vuelve en **{horas}h {minutos}m**.")

    user["last_daily"] = ahora
    ganancia = 1000
    user["balance"] += ganancia
    await guardar_db()

    embed = discord.Embed(title="🎁 ¡Daily reclamado!", color=COLOR)
    embed.add_field(name="Recompensa", value=f"**+${ganancia:,}**")
    embed.set_footer(text="Vuelve mañana para tu siguiente daily")
    await ctx.send(embed=embed)

@bot.command()
async def depositar(ctx, cantidad: int):
    user = get_user(ctx.author.id)

    if cantidad <= 0:
        return await ctx.send("❌ La cantidad debe ser mayor a 0.")
    if cantidad > user["balance"]:
        return await ctx.send(f"❌ No tienes suficiente. Tu cartera: **${user['balance']:,}**")

    user["balance"] -= cantidad
    user["banco"] += cantidad
    await guardar_db()

    await ctx.send(f"🏦 Depositaste **${cantidad:,}** al banco. Banco: **${user['banco']:,}**")

@bot.command()
async def retirar(ctx, cantidad: int):
    user = get_user(ctx.author.id)

    if cantidad <= 0:
        return await ctx.send("❌ La cantidad debe ser mayor a 0.")
    if cantidad > user["banco"]:
        return await ctx.send(f"❌ No tienes suficiente en el banco. Banco: **${user['banco']:,}**")

    user["banco"] -= cantidad
    user["balance"] += cantidad
    await guardar_db()

    await ctx.send(f"💸 Retiraste **${cantidad:,}** del banco. Cartera: **${user['balance']:,}**")

@bot.command()
async def ranking(ctx):
    if not db:
        return await ctx.send("📊 No hay datos aún.")

    top = sorted(db.items(), key=lambda x: x[1]["balance"] + x[1]["banco"], reverse=True)[:5]

    embed = discord.Embed(title="🏆 Top 5 Más Ricos", color=COLOR)
    medallas = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

    for i, (uid, data) in enumerate(top):
        try:
            user = await bot.fetch_user(int(uid))
            nombre = user.display_name
        except Exception:
            nombre = f"Usuario {uid}"
        total = data["balance"] + data["banco"]
        embed.add_field(
            name=f"{medallas[i]} {nombre}",
            value=f"**${total:,}**",
            inline=False
        )

    await ctx.send(embed=embed)

# ════════════════════════════════
# 🎰 SLOTS
# ════════════════════════════════

@bot.command()
async def slots(ctx, apuesta: int):
    user = get_user(ctx.author.id)

    if apuesta <= 0:
        return await ctx.send("❌ La apuesta debe ser mayor a 0.")
    if apuesta > user["balance"]:
        return await ctx.send(f"❌ No tienes suficiente. Cartera: **${user['balance']:,}**")

    user["balance"] -= apuesta

    simbolos = ["🍒", "🍋", "💎", "7️⃣", "⭐", "🍇"]
    resultado = [random.choice(simbolos) for _ in range(3)]

    if resultado[0] == resultado[1] == resultado[2]:
        if resultado[0] == "💎":
            multiplicador = 10
            texto = f"💎 **MEGA JACKPOT** x{multiplicador}!"
        elif resultado[0] == "7️⃣":
            multiplicador = 7
            texto = f"7️⃣ **JACKPOT** x{multiplicador}!"
        else:
            multiplicador = 5
            texto = f"🎉 **TRIPLE** x{multiplicador}!"
        ganancia = apuesta * multiplicador
        user["balance"] += ganancia
        resultado_texto = f"✅ +${ganancia:,}"
    elif resultado[0] == resultado[1] or resultado[1] == resultado[2] or resultado[0] == resultado[2]:
        ganancia = int(apuesta * 1.5)
        user["balance"] += ganancia
        texto = "✨ Par encontrado"
        resultado_texto = f"✅ +${ganancia:,}"
    else:
        texto = "😢 Sin premio"
        resultado_texto = f"❌ -${apuesta:,}"

    await guardar_db()

    embed = discord.Embed(title="🎰 Tragamonedas", color=COLOR)
    embed.add_field(name="Resultado", value=" | ".join(resultado), inline=False)
    embed.add_field(name=texto, value=resultado_texto, inline=False)
    embed.set_footer(text=f"Cartera: ${user['balance']:,}")
    await ctx.send(embed=embed)

# ════════════════════════════════
# 🎡 RULETA
# ════════════════════════════════

@bot.command()
async def ruleta(ctx, apuesta: int, color: str):
    user = get_user(ctx.author.id)

    if apuesta <= 0:
        return await ctx.send("❌ La apuesta debe ser mayor a 0.")
    if apuesta > user["balance"]:
        return await ctx.send(f"❌ No tienes suficiente. Cartera: **${user['balance']:,}**")

    color = color.lower()
    if color not in ["rojo", "negro", "verde"]:
        return await ctx.send("❌ Elige: `rojo`, `negro` o `verde`")

    user["balance"] -= apuesta
    numero = random.randint(0, 36)

    if numero == 0:
        resultado = "verde"
        emoji = "🟢"
    elif numero % 2 == 0:
        resultado = "negro"
        emoji = "⚫"
    else:
        resultado = "rojo"
        emoji = "🔴"

    if color == resultado:
        if resultado == "verde":
            ganancia = apuesta * 14
        else:
            ganancia = apuesta * 2
        user["balance"] += ganancia
        texto = f"✅ Ganaste **+${ganancia:,}**"
    else:
        texto = f"❌ Perdiste **-${apuesta:,}**"

    await guardar_db()

    embed = discord.Embed(title="🎡 Ruleta", color=COLOR)
    embed.add_field(name="Número", value=f"**{numero}** {emoji} {resultado}", inline=False)
    embed.add_field(name="Tu apuesta", value=f"{color} — {texto}", inline=False)
    embed.set_footer(text=f"Cartera: ${user['balance']:,}")
    await ctx.send(embed=embed)

# ════════════════════════════════
# 🃏 BLACKJACK INTERACTIVO
# ════════════════════════════════

MAZO = [2,3,4,5,6,7,8,9,10,10,10,10,11] * 4

def sacar_carta(mano):
    return mano + [random.choice(MAZO)]

def valor_mano(mano):
    total = sum(mano)
    ases = mano.count(11)
    while total > 21 and ases:
        total -= 10
        ases -= 1
    return total

def mano_str(mano):
    return " | ".join(str(c) for c in mano) + f" = **{valor_mano(mano)}**"

@bot.command()
async def bj(ctx, apuesta: int):
    user = get_user(ctx.author.id)

    if apuesta <= 0:
        return await ctx.send("❌ La apuesta debe ser mayor a 0.")
    if apuesta > user["balance"]:
        return await ctx.send(f"❌ No tienes suficiente. Cartera: **${user['balance']:,}**")

    user["balance"] -= apuesta
    await guardar_db()

    mano_jugador = sacar_carta(sacar_carta([]))
    mano_dealer = sacar_carta(sacar_carta([]))

    def make_embed(estado="jugando"):
        embed = discord.Embed(title="🃏 Blackjack", color=COLOR)
        embed.add_field(name="Tu mano", value=mano_str(mano_jugador), inline=False)
        if estado == "jugando":
            embed.add_field(name="Dealer", value=f"{mano_dealer[0]} | ❓", inline=False)
            embed.set_footer(text="Reacciona: ✅ Pedir carta | ❌ Plantarse")
        else:
            embed.add_field(name="Dealer", value=mano_str(mano_dealer), inline=False)
        return embed

    # Blackjack natural
    if valor_mano(mano_jugador) == 21:
        ganancia = int(apuesta * 2.5)
        user["balance"] += ganancia
        await guardar_db()
        embed = make_embed("fin")
        embed.add_field(name="🎴 ¡BLACKJACK!", value=f"+${ganancia:,}", inline=False)
        return await ctx.send(embed=embed)

    msg = await ctx.send(embed=make_embed())
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    while True:
        try:
            reaction, _ = await bot.wait_for(
                "reaction_add",
                timeout=30.0,
                check=lambda r, u: u == ctx.author and str(r.emoji) in ["✅", "❌"] and r.message.id == msg.id
            )
        except asyncio.TimeoutError:
            await msg.edit(content="⏰ Tiempo agotado. Te plantaste automáticamente.")
            break

        if str(reaction.emoji) == "✅":
            mano_jugador = sacar_carta(mano_jugador)
            if valor_mano(mano_jugador) > 21:
                await msg.edit(embed=make_embed("fin"), content="")
                embed = discord.Embed(title="🃏 Blackjack", color=discord.Color.red())
                embed.add_field(name="💥 Te pasaste", value=f"Perdiste **-${apuesta:,}**")
                await ctx.send(embed=embed)
                return
            await msg.edit(embed=make_embed())
        else:
            break  # Se plantó

    # Turno del dealer
    while valor_mano(mano_dealer) < 17:
        mano_dealer = sacar_carta(mano_dealer)

    pj = valor_mano(mano_jugador)
    pd = valor_mano(mano_dealer)

    await msg.edit(embed=make_embed("fin"))

    if pd > 21 or pj > pd:
        ganancia = apuesta * 2
        user["balance"] += ganancia
        resultado = f"✅ ¡Ganaste **+${ganancia:,}**!"
    elif pj == pd:
        user["balance"] += apuesta
        resultado = f"🤝 Empate. Recuperas **${apuesta:,}**"
    else:
        resultado = f"❌ Perdiste **-${apuesta:,}**"

    await guardar_db()

    embed = discord.Embed(title="🃏 Resultado", color=COLOR)
    embed.add_field(name="Tú", value=str(pj), inline=True)
    embed.add_field(name="Dealer", value=str(pd), inline=True)
    embed.add_field(name="Resultado", value=resultado, inline=False)
    embed.set_footer(text=f"Cartera: ${user['balance']:,}")
    await ctx.send(embed=embed)

# ════════════════════════════════
# 🪙 COINFLIP
# ════════════════════════════════

@bot.command()
async def coinflip(ctx, apuesta: int, eleccion: str):
    user = get_user(ctx.author.id)

    if apuesta <= 0:
        return await ctx.send("❌ La apuesta debe ser mayor a 0.")
    if apuesta > user["balance"]:
        return await ctx.send(f"❌ No tienes suficiente. Cartera: **${user['balance']:,}**")

    eleccion = eleccion.lower()
    if eleccion not in ["cara", "cruz"]:
        return await ctx.send("❌ Elige `cara` o `cruz`")

    user["balance"] -= apuesta
    resultado = random.choice(["cara", "cruz"])

    if eleccion == resultado:
        ganancia = apuesta * 2
        user["balance"] += ganancia
        texto = f"✅ ¡Ganaste **+${ganancia:,}**!"
    else:
        texto = f"❌ Perdiste **-${apuesta:,}**"

    await guardar_db()

    emoji = "👑" if resultado == "cara" else "🦅"
    embed = discord.Embed(title="🪙 Coinflip", color=COLOR)
    embed.add_field(name=f"{emoji} Salió: **{resultado}**", value=texto, inline=False)
    embed.set_footer(text=f"Cartera: ${user['balance']:,}")
    await ctx.send(embed=embed)

# ════════════════════════════════
# 🎲 DADOS
# ════════════════════════════════

@bot.command()
async def dados(ctx, apuesta: int, numero: int):
    user = get_user(ctx.author.id)

    if apuesta <= 0:
        return await ctx.send("❌ La apuesta debe ser mayor a 0.")
    if apuesta > user["balance"]:
        return await ctx.send(f"❌ No tienes suficiente. Cartera: **${user['balance']:,}**")
    if numero < 2 or numero > 12:
        return await ctx.send("❌ Elige un número entre 2 y 12.")

    user["balance"] -= apuesta
    d1 = random.randint(1, 6)
    d2 = random.randint(1, 6)
    total = d1 + d2

    if total == numero:
        # Multiplicadores según dificultad
        multiplicadores = {2: 10, 3: 8, 4: 6, 5: 5, 6: 4, 7: 3, 8: 4, 9: 5, 10: 6, 11: 8, 12: 10}
        mult = multiplicadores[numero]
        ganancia = apuesta * mult
        user["balance"] += ganancia
        texto = f"✅ ¡Ganaste **+${ganancia:,}** (x{mult})!"
    else:
        texto = f"❌ Perdiste **-${apuesta:,}**"

    await guardar_db()

    embed = discord.Embed(title="🎲 Dados", color=COLOR)
    embed.add_field(name="Resultado", value=f"🎲 {d1} + 🎲 {d2} = **{total}**", inline=False)
    embed.add_field(name="Tu número", value=str(numero), inline=True)
    embed.add_field(name="Resultado", value=texto, inline=False)
    embed.set_footer(text=f"Cartera: ${user['balance']:,}")
    await ctx.send(embed=embed)

# ════════════════════════════════
# 🚀 EVENTO
# ════════════════════════════════

@bot.event
async def on_ready():
    cargar_db()
    print(f"✅ {bot.user} conectado")
    print(f"📡 Servidores: {len(bot.guilds)}")

bot.run(TOKEN)