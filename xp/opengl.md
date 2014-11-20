<todo>
* http://user.xmission.com/~nate/tutors.html
* OpenGL超级宝典 Richard S.Wright Jr Benjamin Lipcha
* http://www.arcsynthesis.org/gltut/index.html
* http://mkhgg.blog.51cto.com/1741572/663271
</todo>

<resource>
* http://opengl-redbook.com/

</resource>

<xp>
* opengl version
sudo apt-get install mesa-utils
glxinfo | grep "OpenGL version"

*
sudo apt-get install freeglut3 freeglut3-dev libglew-dev libxmu-dev libxi-dev
*
g++ -I../include  triangles.cpp -lglut -lGLU -lGL -lGLEW
g++ triangles.cpp LoadShaders.cpp -lGL -lGLU -lGLEW -lglut -o triangles
g++ test1.cpp -lGL -lGLU -lGLEW -lglut -o test1

* glClear缺省是黑色
* glFlush并不等待完成，而glFinish会。
</xp>