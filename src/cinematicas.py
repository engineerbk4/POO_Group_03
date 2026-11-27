"""Cinematicas tipo comic interactivo, basadas en el storyboard de Mision en Marte.
ENTER/ESPACIO: siguiente pagina; ESC: omitir. Sin dependencias adicionales.
"""
from __future__ import annotations
import math
import random
from pathlib import Path
import pygame

W,H=960,640
BG=(8,7,16); INK=(25,18,37); DEEP=(38,25,50); EDGE=(111,68,105)
CREAM=(250,220,181); MUTED=(192,157,179); PEACH=(246,160,139)
RED=(188,76,96); GOLD=(255,203,133); PURPLE=(129,77,129)

STORIES={
 'intro':[
  ('SIRIUS','ÚLTIMA LUZ','Nunca imaginé...','que vería apagarse una estrella.'),
  ('CITY','NOCTIS IV','Mi planeta se está quedando','sin tiempo...'),
  ('MAP','ARCHIVO / NOX','El Nox alimenta nuestras máquinas y puede salvar a Sirius.','Detectamos su señal en Marte.'),
  ('EXPLORADOR','EXPLORADOR','Soy parte del equipo científico de Noctis IV.','No pensaba hacer este viaje. Pero aquí estoy.'),
  ('SHIP','RUMBO A MARTE','Si la nave sobrevive,','yo también debería hacerlo, ¿no?'),
  ('MARS','ATERRIZAJE','¡La nave ha sufrido daños!','Necesito combustible y un refugio. Hay señales de vida cerca.'),
  ('ALIEN','PRIMER CONTACTO','Tengo compañía. Parece que le doy miedo.','Tal vez podamos ayudarnos.')],
 'nivel1':[
  ('BRIEF','TRES REFUGIOS','Las primeras muestras están a salvo en la nave.','Construiré tres bases para proteger la extracción.')],
 'nivel2':[
  ('CRYSTAL','NOX RECUPERADO','Las bases resistieron.','El Nox está a nuestro alcance.'),
  ('BRIEF','ÚLTIMA OPORTUNIDAD','El Nox está asegurado, pero aún falta combustible.','Debo regresar al cohete antes de que las tormentas me alcancen.')],
 'final':[
  ('RETURN','REGRESO','Al fin de vuelta a casa...','Llevo el Nox conmigo.'),
  ('SAVED','SIRIUS','Salvé Sirius y mi planeta.','Todavía tenemos un futuro.')]
}

class Cinematica:
 def __init__(self,nombre):
  self.escenas=STORIES[nombre];self.indice=0;self.t=0.;self.terminada=False;self.revelado=False
  self.title=pygame.font.SysFont('georgia,cambria',42,bold=True)
  self.head=pygame.font.SysFont('georgia,cambria',31,bold=True)
  self.body=pygame.font.SysFont('trebuchetms,verdana',26)
  self.small=pygame.font.SysFont('trebuchetms,verdana',21)
  self.meta=pygame.font.SysFont('consolas,couriernew',17,bold=True)
  base=Path(__file__).resolve().parent.parent/'assets'
  self.explorador=[pygame.image.load(str(base/f'explorador_comic_{i}.png')).convert_alpha() for i in range(5)]
  self.alien=[pygame.image.load(str(base/f'marciano_comic_{i}.png')).convert_alpha() for i in range(5)]
  self.scared=[pygame.image.load(str(base/f'marciano_asustado_{i}.png')).convert_alpha() for i in range(5)]
  rng=random.Random(451)
  self.stars=[(rng.randrange(W),rng.randrange(H),rng.choice([1,1,2,2,3]),rng.random()*6.28) for _ in range(120)]
  self.grain=[(rng.randrange(W),rng.randrange(H),rng.choice([EDGE,DEEP,INK])) for _ in range(400)]
 def textoCompleto(self):
  kind,_,a,b=self.escenas[self.indice]
  bloques={
   'EXPLORADOR':[(a,.3),(b,1.8)], 'BRIEF':[(a,.3),(b,1.6)],
   'MARS':[(a,.25),(b,1.2)], 'CRYSTAL':[(a,.4),(b,1.1)],
   'ALIEN':[('Tengo compañía.',.2),('Parece que le doy miedo.',1.1),('Tal vez podamos ayudarnos.',2.)],
   'RETURN':[(a+' '+b,.35)], 'SAVED':[(a+' '+b,.45)]}
  return self.revelado or all(self.t >= delay+len(texto)/55 for texto,delay in bloques.get(kind,[(a+' '+b,.3)]))
 def avanzar(self):
  if not self.textoCompleto():
   self.revelado=True;return
  self.indice+=1;self.t=0;self.revelado=False
  if self.indice>=len(self.escenas):self.terminada=True
 def update(self,dt):self.t+=min(dt,.1)
 def txt(self,s,text,x,y,font=None,color=CREAM):
  font=font or self.body;s.blit(font.render(text,True,color),(int(x),int(y)))
 def wrap(self,text,font,maxw):
  lines=[];line=''
  for word in text.split():
   trial=(line+' '+word).strip()
   if font.size(trial)[0]>maxw and line:lines.append(line);line=word
   else:line=trial
  if line:lines.append(line)
  return lines
 def textblock(self,s,text,rect,font=None,color=CREAM,delay=.15,spacing=6):
  x,y,w,h=rect;font=font or self.body
  lines=self.wrap(text,font,w)
  for size in range(24,10,-2):
   if len(lines)*font.get_linesize()+max(0,len(lines)-1)*spacing<=h:break
   font=pygame.font.SysFont('trebuchetms,verdana,arial',size)
   lines=self.wrap(text,font,w)
  n=len(text) if self.revelado else max(0,int((self.t-delay)*55))
  for i,line in enumerate(lines):
   if n<=0:break
   self.txt(s,line[:n],x,y+i*(font.get_linesize()+spacing),font,color)
   n-=len(line)+1
 def panel(self,s,rect,fill=INK,border=EDGE):
  pygame.draw.rect(s,fill,rect,border_radius=5)
  pygame.draw.rect(s,border,rect,3,border_radius=5)
 def speech(self,s,text,rect,delay=.3,style='normal'):
  x,y,w,h=rect
  if style=='burst':
   # Bocadillo alto y ancho: picos en el exterior, centro despejado para el texto.
   cx=x+w/2;cy=y+h/2
   pts=[]
   for i in range(32):
    ang=-math.pi/2+i*math.tau/32
    r=1 if i%2==0 else .86
    pts.append((int(cx+math.cos(ang)*(w/2)*r),int(cy+math.sin(ang)*(h/2)*r)))
   pygame.draw.polygon(s,DEEP,pts)
   pygame.draw.lines(s,PEACH,True,pts,3)
   # Centro seguro: nunca dibujar el texto encima de los picos.
   safe_w=int(w*.65)
   f=self.body
   for size in range(24,14,-2):
    if len(self.wrap(text,f,safe_w))*f.get_linesize()<=h*.55:break
    f=pygame.font.SysFont('trebuchetms,verdana',size,bold=True)
   lines=self.wrap(text,f,safe_w)
   y0=cy-(len(lines)*f.get_linesize())/2
   n=len(text) if self.revelado else max(0,int((self.t-delay)*55));visible=text[:n]
   for i,line in enumerate(self.wrap(visible,f,safe_w)):
    rendered=f.render(line,True,CREAM)
    s.blit(rendered,(int(cx-rendered.get_width()/2),int(y0+i*f.get_linesize())))
   return
  else:
   pygame.draw.rect(s,DEEP,rect,border_radius=19)
   pygame.draw.rect(s,PURPLE,rect,3,border_radius=19)
   pygame.draw.polygon(s,DEEP,[(x+round(w*.24),y+h-2),(x+round(w*.31),y+h+19),(x+round(w*.39),y+h-2)])
   pygame.draw.lines(s,PURPLE,False,[(x+round(w*.24),y+h-2),(x+round(w*.31),y+h+19),(x+round(w*.39),y+h-2)],3)
  f=self.small
  for size in range(20,12,-2):
   if f.get_linesize()*len(self.wrap(text,f,w-44))<=h-25:break
   f=pygame.font.SysFont('trebuchetms,verdana',size)
  self.textblock(s,text,(x+22,y+max(12,(h-f.get_height()*len(self.wrap(text,f,w-44)))/2),w-44,h-18),f,CREAM,delay,2)

 def stars_draw(self,s):
  for x,y,r,p in self.stars:
   if math.sin(self.t*1.5+p)>-.65:
    xx=(x-int(self.t*4*r))%W
    pygame.draw.rect(s,GOLD if r==3 else MUTED,(xx,y,r,r))
 def texture(self,s):
  # Sparse pixel grain gives a printed comic / retro sci-fi texture.
  for x,y,c in self.grain:
   if (x+y)%3:pygame.draw.rect(s,c,(x,y,2,2))
 def planet(self,s,x,y,r,base=RED,glow=False):
  x=int(x);y=int(y);r=int(r)
  if glow:
   for extra,c in [(32,DEEP),(20,EDGE),(9,PURPLE)]:pygame.draw.circle(s,c,(x,y),r+extra)
  pygame.draw.circle(s,base,(x,y),r)
  for i in range(9):
   yy=y-r+int((i+.5)*2*r/9)
   width=int(math.sqrt(max(0,r*r-(yy-y)**2)))
   if width>10:pygame.draw.line(s,PEACH if i%3==0 else base,(x-width//2,yy),(x+width//2,yy),2)
  pygame.draw.circle(s,(231,132,127),(x-r//4,y-r//4),max(8,r//5))
 def figure(self,s,who,rect,frame=None):
  x,y,w,h=rect
  images=self.explorador if who=='EXPLORADOR' else self.scared if who=='SCARED' else self.alien
  if frame is None:frame=int(self.t*3)%5
  spr=images[frame%len(images)]
  sw,sh=spr.get_size();fac=min(w/sw,h/sh)
  out=pygame.transform.scale(spr,(max(1,round(sw*fac)),max(1,round(sh*fac))))
  s.blit(out,(int(x+(w-out.get_width())/2),int(y+(h-out.get_height())/2+math.sin(self.t*2)*3)))
 def line(self,s,a,b,c=GOLD,width=3):pygame.draw.line(s,c,a,b,width)
 def diamond(self,s,x,y,r=12,c=GOLD):
  pygame.draw.polygon(s,c,[(x,y-r),(x+r,y),(x,y+r),(x-r,y)])
  pygame.draw.lines(s,CREAM,True,[(x,y-r),(x+r,y),(x,y+r),(x-r,y)],2)
 def scene(self,s,kind,title,a,b):
  wave=math.sin(self.t*1.2)
  if kind=='SIRIUS':
   self.txt(s,'01 / PRÓLOGO',52,42,self.meta,PEACH)
   self.txt(s,'ÚLTIMA LUZ',52,82,self.title,CREAM)
   x,y=690,285
   for r in range(190,75,-5):
    k=(190-r)/115; c=tuple(int(BG[i]+(RED[i]-BG[i])*k*k*.75) for i in range(3))
    pygame.draw.circle(s,c,(x,y),r)
   for i in range(36):
    ang=i*math.tau/36; r=98+18*math.sin(i*3+self.t*2)
    pts=[(int(x+math.cos(ang+d)*rr),int(y+math.sin(ang+d)*rr)) for d,rr in [(-.06,78),(0,r),(.06,78)]]
    pygame.draw.polygon(s,PEACH if i%3==0 else RED,pts)
   for r,c in [(83,RED),(72,PEACH),(54,GOLD)]:pygame.draw.circle(s,c,(x,y),r+int(wave*3))
   for i in range(25):
    ang=i*2.4; r=105+(i*17+self.t*18)%85
    pygame.draw.circle(s,GOLD,(int(x+math.cos(ang)*r),int(y+math.sin(ang)*r)),1+i%3)
   self.textblock(s,a+' '+b,(55,205,380,180),self.head,CREAM,.3)
   self.panel(s,(55,420,365,100),INK)
   self.txt(s,'SIRIUS / ESTADO CRÍTICO',72,437,self.meta,PEACH)
   pygame.draw.rect(s,DEEP,(72,475,330,10));pygame.draw.rect(s,RED,(72,475,max(15,110-int(self.t*8)),10))
  elif kind=='CITY':
   self.txt(s,'02 / ARCHIVO PLANETARIO',52,42,self.meta,PEACH)
   self.txt(s,'NOCTIS IV',52,82,self.title,CREAM)
   self.planet(s,755,155,92,PURPLE,True)
   for layer in range(3):
    rng=random.Random(90+layer); step=28+layer*15
    for i,x in enumerate(range(-20,W,step)):
     hh=rng.randrange(65,170)+layer*45; bottom=470+layer*55
     pygame.draw.rect(s,[(44,30,55),(59,36,65),(78,43,68)][layer],(x,bottom-hh,step-4,hh))
     for j in range(5):
      yy=bottom-hh+15+j*27
      if yy<bottom-10 and (i*7+j*3)%11>min(8,int(self.t)):
       pygame.draw.rect(s,PEACH,(x+8,yy,4,9))
   self.panel(s,(52,175,440,120),INK)
   self.textblock(s,a+' '+b,(73,195,395,85),self.body,CREAM,.3)
  elif kind=='MAP':
   self.txt(s,'03 / SEÑAL INTERCEPTADA',52,42,self.meta,PEACH)
   self.txt(s,'OPERACIÓN NOX',52,80,self.title,CREAM)
   self.panel(s,(52,150,856,295),DEEP)
   for x in range(75,900,35):self.line(s,(x,165),(x,430),INK,1)
   for y in range(165,430,35):self.line(s,(65,y),(895,y),INK,1)
   self.planet(s,235,290,57,PURPLE);self.planet(s,725,285,91,RED)
   self.line(s,(302,290),(624,285),MUTED,2)
   for i in range(10):self.diamond(s,315+i*30,290,3,PEACH)
   self.diamond(s,315+int((self.t*80)%300),290,8,GOLD)
   pygame.draw.circle(s,GOLD,(725,285),98+int((self.t*22)%24),2)
   self.txt(s,'NOCTIS IV',190,370,self.meta,CREAM);self.txt(s,'MARTE',700,395,self.meta,CREAM)
   self.panel(s,(52,465,856,116),INK)
   self.txt(s,'EXPLORADOR / TRANSMISIÓN',73,479,self.meta,PEACH)
   self.textblock(s,a+' '+b,(73,508,810,65),self.body,CREAM,.3,2)
  elif kind=='EXPLORADOR':
   self.txt(s,'04 / PERSONAL DE MISIÓN',52,42,self.meta,PEACH)
   self.panel(s,(52,85,390,500),DEEP)
   pygame.draw.circle(s,EDGE,(247,320),155,2)
   pygame.draw.circle(s,INK,(247,320),140)
   self.figure(s,'EXPLORADOR',(82,130,330,420),int(self.t*2)%5)
   self.txt(s,'EXPLORADOR',485,110,self.title,GOLD)
   self.txt(s,'EXPLORADOR / EQUIPO CIENTÍFICO',485,169,self.meta,PEACH)
   self.line(s,(485,200),(900,200),EDGE,2)
   self.textblock(s,a,(485,230,405,125),self.body,CREAM,.3)
   self.textblock(s,b,(485,365,405,135),self.body,CREAM,1.8)
  elif kind=='SHIP':
   self.txt(s,'05 / TRAYECTORIA DE VUELO',52,42,self.meta,PEACH)
   self.planet(s,770,280,145,RED,True)
   x=180+min(250,self.t*38);y=275+wave*8
   for i in range(28):
    xx=int((i*83-self.t*180)%W); yy=90+(i*47)%340
    self.line(s,(xx,yy),(xx+18+i%12,yy),EDGE,2)
   pygame.draw.polygon(s,EDGE,[(x-65,y-25),(x-95,y-65),(x+15,y-30),(x+65,y)])
   pygame.draw.polygon(s,EDGE,[(x-65,y+25),(x-95,y+65),(x+15,y+30),(x+65,y)])
   pygame.draw.polygon(s,CREAM,[(x-80,y-22),(x+45,y-28),(x+110,y),(x+45,y+28),(x-80,y+22)])
   pygame.draw.ellipse(s,PURPLE,(x+15,y-15,48,30));pygame.draw.ellipse(s,PEACH,(x+21,y-10,32,17))
   pygame.draw.rect(s,RED,(x-95,y-18,25,36))
   pygame.draw.polygon(s,PEACH,[(x-95,y-15),(x-155-int(wave*15),y),(x-95,y+15)])
   pygame.draw.polygon(s,GOLD,[(x-95,y-8),(x-130,y),(x-95,y+8)])
   self.panel(s,(52,465,856,116),INK)
   self.txt(s,'EXPLORADOR / CANAL DE VUELO',73,479,self.meta,PEACH)
   self.textblock(s,a+' '+b,(73,510,810,65),self.body,CREAM,.3)
  elif kind=='MARS':
   self.planet(s,720,205,120,RED)
   pygame.draw.polygon(s,EDGE,[(0,500),(110,385),(220,445),(355,340),(475,495),(650,400),(960,490),(960,640),(0,640)])
   self.figure(s,'EXPLORADOR',(90,280,210,315))
   self.panel(s,(52,45,530,120),INK)
   self.txt(s,"ALERTA / ATERRIZAJE DE EMERGENCIA",72,62,self.meta,PEACH)
   self.textblock(s,a,(72,95,490,60),self.body,CREAM,.25)
   self.speech(s,b,(395,447,505,135),1.2)

  elif kind=='ALIEN':
   # Dos personajes completos y legibles; subtítulos como cómic sin tapar los sprites.
   pygame.draw.polygon(s,DEEP,[(50,118),(465,105),(438,558),(50,558)])
   pygame.draw.lines(s,PURPLE,True,[(50,118),(465,105),(438,558),(50,558)],3)
   pygame.draw.polygon(s,INK,[(486,105),(914,118),(914,558),(457,558)])
   pygame.draw.lines(s,PURPLE,True,[(486,105),(914,118),(914,558),(457,558)],3)
   for pts,center,col in [([(50,118),(465,105),(438,558),(50,558)],(220,340),(128,57,75)), ([(486,105),(914,118),(914,558),(457,558)],(740,340),(42,105,113))]:
    aura=pygame.Surface((W,H),pygame.SRCALPHA)
    for r in range(220,10,-5):
     k=1-r/220;pygame.draw.circle(aura,(*col,int(110*k)),center,r)
    mask=pygame.Surface((W,H),pygame.SRCALPHA);pygame.draw.polygon(mask,(255,255,255,255),pts)
    aura.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MULT);s.blit(aura,(0,0))
   self.figure(s,'EXPLORADOR',(92,185,275,335),0)
   self.figure(s,'SCARED',(620,162,250,362),0)
   # Encabezado libre; líneas de diálogo en espacios vacíos, sin cajas.
   self.txt(s,'PRIMER CONTACTO',310,36,self.meta,PEACH)
   self.textblock(s,'Tengo compañía.',(95,135,330,40),self.small,CREAM,.2)
   self.textblock(s,'Parece que le doy miedo.',(494,135,415,44),self.small,CREAM,1.1)
   if self.revelado or self.t >= 2.0:
    pts=[(340,272),(620,272),(620,280),(636,296),(620,312),(620,320),(340,320),(340,312),(324,296),(340,280)]
    pygame.draw.polygon(s,INK,pts)
    pygame.draw.lines(s,EDGE,True,pts,3)
    inner=[(344,277),(616,277),(616,283),(628,296),(616,309),(616,315),(344,315),(344,309),(332,296),(344,283)]
    pygame.draw.lines(s,GOLD,True,inner,1)
    self.diamond(s,480,272,5,GOLD)
    self.diamond(s,480,320,5,GOLD)
    frase='Tal vez podamos ayudarnos.'
    ancho=self.small.size(frase)[0]
    self.textblock(s,frase,(480-ancho//2,284,ancho+8,32),self.small,CREAM,2.0)
  elif kind=='CRYSTAL':
   # Marte domina la escena; los minerales Nox orbitan a su alrededor.
   self.planet(s,490,308,194,RED,True)
   rng=random.Random(72)
   for i in range(42):
    ang=i*math.tau/42
    rr=160+rng.randint(-15,20)
    xx=490+math.cos(ang)*rr;yy=308+math.sin(ang)*rr*.88
    pygame.draw.circle(s,(150,56,79),(int(xx),int(yy)),rng.randint(4,12),2)
   for i in range(12):
    ang=i*math.tau/12+self.t*.09
    radius=228+(i%3)*18
    x=int(490+radius*math.cos(ang));y=int(308+radius*.83*math.sin(ang))
    self.diamond(s,x,y,10+(i%3)*3,PEACH if i%2 else GOLD)
   self.speech(s,a,(60,105,310,90),.4)
   self.speech(s,b,(625,448,285,105),1.1)
  elif kind=='BRIEF':
   self.panel(s,(80,75,800,480),INK)
   self.txt(s,'// BITÁCORA DE MISIÓN',120,110,self.meta,PEACH)
   self.txt(s,title,120,155,self.title,GOLD)
   self.figure(s,'EXPLORADOR',(105,235,240,290))
   self.textblock(s,a,(385,245,440,125),self.body,CREAM,.3)
   self.textblock(s,b,(385,385,440,135),self.body,CREAM,1.6)
  elif kind=='RETURN':
   self.planet(s,745,335,170,PURPLE)
   x=200+min(280,self.t*45);y=215+wave*8
   pygame.draw.polygon(s,CREAM,[(x+90,y),(x-55,y-38),(x-35,y),(x-55,y+38)])
   for i in range(5):self.line(s,(x-70-i*20,y),(x-90-i*30,y),RED,3)
   self.textblock(s,a+' '+b,(70,350,340,170),self.head,CREAM,.35)
   # Sin etiqueta inferior: el Nox se representa con un cristal flotante.
   self.diamond(s,540,440,19,GOLD)
  elif kind=='SAVED':
   self.planet(s,480,310,185,RED,True)
   pygame.draw.circle(s,GOLD,(480,310),95+int(wave*5))
   for i in range(13):
    theta=i*math.tau/13+self.t*.15
    self.diamond(s,int(480+260*math.cos(theta)),int(310+240*math.sin(theta)),5,PEACH)
   self.panel(s,(90,485,785,108),INK)
   self.textblock(s,a+' '+b,(135,506,700,80),self.head,CREAM,.45)
 def draw(self,pantalla):
  if self.terminada:return
  s=pantalla;s.fill(BG);self.stars_draw(s)
  kind,title,a,b=self.escenas[self.indice]
  self.scene(s,kind,title,a,b)
  # Edge lines and grain, plus a slim unobtrusive navigation strip.
  self.texture(s)
  pygame.draw.rect(s,BG,(0,605,W,35))
  pygame.draw.line(s,EDGE,(0,604),(960,604),2)
  self.txt(s,f'{self.indice+1:02}/{len(self.escenas):02}',30,613,self.meta,MUTED)
  self.txt(s,'ESC: OMITIR',375,613,self.meta,MUTED)
  self.txt(s,'ENTER: AVANZAR' if self.textoCompleto() else 'ENTER: MOSTRAR',740,613,self.meta,GOLD)
  # A brief page-turn flash, then the complete panel becomes visible.
  if self.t<.20:
   cover=pygame.Surface((W,H),pygame.SRCALPHA)
   cover.fill((*BG,int(255*(1-self.t/.20))))
   s.blit(cover,(0,0))
