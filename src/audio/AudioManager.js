/**
 * 音效管理类
 * 管理游戏音效播放
 */

export class AudioManager {
    constructor() {
        this.sounds = {};
        this.enabled = true;
        this.volume = 0.5;
        this.init();
    }

    init() {
        console.log('🔊 音效系统初始化');
        
        // 这里使用占位音效，实际项目需要加载真实音频文件
        // 可以使用 Laya.SoundManager 加载
        /*
        Laya.SoundManager.playMusic("res/audio/bgm.mp3", 0);
        this.sounds.jump = Laya.SoundManager.playSound("res/audio/jump.mp3");
        this.sounds.score = Laya.SoundManager.playSound("res/audio/score.mp3");
        this.sounds.gameover = Laya.SoundManager.playSound("res/audio/gameover.mp3");
        */
    }

    play(soundName) {
        if (!this.enabled) return;
        
        console.log(`🔊 播放音效：${soundName}`);
        
        // 实际项目中播放真实音效
        // Laya.SoundManager.playSound(`res/audio/${soundName}.mp3`);
        
        // 临时使用控制台日志
        switch (soundName) {
            case 'jump':
                console.log('  💫 跳跃音效');
                break;
            case 'score':
                console.log('  ✨ 得分音效');
                break;
            case 'gameover':
                console.log('  💀 游戏结束音效');
                break;
            case 'perfect':
                console.log('  🌟 完美落地音效');
                break;
        }
    }

    playMusic(musicName, loop = true) {
        if (!this.enabled) return;
        
        console.log(`🎵 播放音乐：${musicName}`);
        // Laya.SoundManager.playMusic(`res/audio/${musicName}.mp3`, loop ? 0 : 1);
    }

    setVolume(vol) {
        this.volume = Math.max(0, Math.min(1, vol));
        Laya.SoundManager.musicVolume = this.volume;
        Laya.SoundManager.soundVolume = this.volume;
    }

    toggle() {
        this.enabled = !this.enabled;
        if (!this.enabled) {
            Laya.SoundManager.musicVolume = 0;
            Laya.SoundManager.soundVolume = 0;
        } else {
            Laya.SoundManager.musicVolume = this.volume;
            Laya.SoundManager.soundVolume = this.volume;
        }
        return this.enabled;
    }

    destroy() {
        Laya.SoundManager.stopAll();
    }
}

// 导出单例
export const audioManager = new AudioManager();
